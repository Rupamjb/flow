"""
The Flow Engine - Main Backend
FastAPI server that orchestrates the Flow State logic, integrates with the Chrome Extension,
manages the database, and controls the blocker overlay.
"""

import os
import sys
import time
import json
import asyncio
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from contextlib import asynccontextmanager
import platform
try:
    import winreg  # type: ignore
except Exception:
    winreg = None

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

"""
NOTE: Logging must be initialized before any try/except that logs warnings.
"""
# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("flow_engine.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("FlowEngine")

# Import local modules
from database import (
    init_supabase, get_or_create_user, create_session, update_session,
    get_recent_sessions, update_user_xp, Session, User,
    get_user_status, update_onboarding_data, increment_sessions_count,
    update_cognitive_profile, update_baseline, create_user_with_auth,
    authenticate_user, get_user_by_id, update_mission_log
)
import database as db_module
from window_monitor import WindowMonitor
from notification_suppressor import NotificationSuppressor
from interventions import InterventionManager
from blocker import FlowBlocker
from ai_classifier import get_classifier
try:
    from input_monitor import InputMonitor
    INPUT_MONITOR_AVAILABLE = True
except ImportError:
    INPUT_MONITOR_AVAILABLE = False
    logger.warning("input_monitor not available. Layer 3 detection disabled.")

try:
    from soft_reset import SoftReset
    SOFT_RESET_AVAILABLE = True
except ImportError:
    SOFT_RESET_AVAILABLE = False
    logger.warning("soft_reset not available. Cognitive reset disabled.")

try:
    from local_db import get_db
    from pattern_analyzer import get_analyzer
    LOCAL_DB_AVAILABLE = True
except ImportError:
    LOCAL_DB_AVAILABLE = False
    logger.warning("local_db not available. Pattern learning disabled.")

# Configuration
OFFLINE_MODE = False  # Set to True to bypass Supabase
FLOW_BASELINE_MINUTES = 25
XP_PER_MINUTE = 5
XP_RESUME_BONUS = 10
XP_BREAK_PENALTY = 0

# State Management
class FlowState:
    def __init__(self):
        self.is_running = False
        self.current_session_id: Optional[int] = None
        self.start_time: Optional[datetime] = None
        self.user: Optional[User] = None
        self.current_focus_score = 100.0
        self.apm_history = []
        self.active_window = {"title": "Unknown", "process": "Unknown"}
        self.last_browser_url = ""
        self.last_browser_tab_id = None  # Track last browser tab for closing
        self.distraction_count = 0
        self.resilience_score = 0
        self.stamina_score = 0
        self.energy_level = 100.0  # 0-100%
        self.config = {}
        
        # Layer 3: Input monitoring
        self.current_apm = 0.0
        self.mouse_velocity = 0.0
        self.activity_pattern = "idle"  # 'active', 'passive', 'idle'
        self.active_streak_start: Optional[datetime] = None
        
        # Cognitive fatigue tracking
        self.fatigue_score = 0.0  # 0-100
        self.baseline_apm = 0.0
        self.apm_degradation_count = 0
        self.erratic_movement_count = 0

        # System settings
        self.dnd_prev_value: Optional[int] = None  # previous toast setting
        self.focus_assist_prev_value: Optional[int] = None  # previous Focus Assist level
        
        # Resilience decay tracking
        self.current_distracting_app: Optional[str] = None  # App/URL currently being used despite intervention
        self.distracting_start_time: Optional[datetime] = None  # When user started using distracting content
        self.last_decay_check: Optional[datetime] = None  # Last time we checked for decay
        self.pending_close_tab: bool = False  # Flag for extension to close tab on WAIT FOR BREAK
        
        # Tri-layer flow detection state
        self.layer1_productive_start: Optional[datetime] = None  # When productive app usage started
        self.layer2_last_distraction: Optional[datetime] = None  # Last time a distracting URL was seen
        self.flow_detection_threshold_seconds: int = 600  # Default 10 minutes

state = FlowState()

# Load Config
CONFIG_FILE = "user_config.json"
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                state.config = json.load(f)
                logger.info("User configuration loaded.")
                # Load flow detection threshold
                flow_threshold_minutes = state.config.get("flow_threshold_minutes", 10)
                state.flow_detection_threshold_seconds = flow_threshold_minutes * 60
                logger.info(f"Flow detection threshold set to {flow_threshold_minutes} minutes ({state.flow_detection_threshold_seconds} seconds)")
                return True
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
    return False

# Run Onboarding if needed
if not load_config():
    logger.info("Configuration not found. Please run onboarding.")
    # In a real headless app, we might wait or trigger it via tray
    # For now, we assume tray.py handles the initial onboarding launch
    pass

# Initialize components
window_monitor = WindowMonitor()
intervention_manager = InterventionManager()

# Input monitor and blocker will be initialized later after callback functions are defined
input_monitor = None
blocker = None


# Initialize notification suppressor
try:
    notification_suppressor = NotificationSuppressor()
    logger.info("Notification suppressor initialized")
except Exception as e:
    logger.warning(f"Notification suppressor unavailable: {e}")
    notification_suppressor = None

# Initialize input monitor if available
if INPUT_MONITOR_AVAILABLE:
    def on_input_update(data):
        state.current_apm = data['apm']
        state.activity_pattern = 'active' if data['keyboard_events'] > 30 else 'passive'
        # Track continuous active streak (Layer 3)
        now = datetime.now()
        if state.activity_pattern == 'active':
            if state.active_streak_start is None:
                state.active_streak_start = now
                logger.debug("Layer 3: Active input streak started")
        else:
            # Reset streak if activity becomes passive
            if state.active_streak_start is not None:
                logger.debug("Layer 3: Active input streak ended")
            state.active_streak_start = None

        # Check tri-layer detection if not running
        if not state.is_running:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.run_coroutine_threadsafe(_check_and_auto_start_flow(), loop)
                else:
                    threading.Thread(target=lambda: asyncio.run(_check_and_auto_start_flow()), daemon=True).start()
            except RuntimeError:
                try:
                    loop = asyncio.get_running_loop()
                    asyncio.run_coroutine_threadsafe(_check_and_auto_start_flow(), loop)
                except RuntimeError:
                    threading.Thread(target=lambda: asyncio.run(_check_and_auto_start_flow()), daemon=True).start()

        # Call fatigue detection on each input update (only during flow)
        detect_cognitive_fatigue()
    
    try:
        input_monitor = InputMonitor(callback=on_input_update)
        logger.info("Input monitor initialized (Layer 3 active)")
    except Exception as e:
        logger.warning(f"Failed to initialize input monitor: {e}")
        input_monitor = None

# Initialize soft reset if available
soft_reset = None
if SOFT_RESET_AVAILABLE:
    try:
        duration = int(state.config.get("soft_reset_seconds", 45))
    except Exception:
        duration = 45
    soft_reset = SoftReset(duration=duration)
    logger.info(f"Soft reset system initialized (duration={duration}s)")

# Initialize local database and pattern analyzer
local_db = None
pattern_analyzer = None
if LOCAL_DB_AVAILABLE:
    local_db = get_db()
    pattern_analyzer = get_analyzer()
    logger.info("Local database and pattern analyzer initialized")

# AI Classifier
classifier = get_classifier()

# ============================================================================
# LOGIC HANDLERS
# ============================================================================

def detect_cognitive_fatigue():
    """
    Analyze input patterns to detect cognitive fatigue.
    Updates state.fatigue_score (0-100).
    
    Indicators:
    - APM degradation over time
    - Erratic mouse movements
    - Aimless scrolling patterns
    """
    if not state.is_running or not input_monitor:
        return
    
    # Initialize baseline APM on first session
    if state.baseline_apm == 0 and state.current_apm > 10:
        state.baseline_apm = state.current_apm
        logger.info(f"Baseline APM set: {state.baseline_apm:.1f}")
        return
    
    # Calculate APM degradation
    if state.baseline_apm > 0:
        apm_ratio = state.current_apm / state.baseline_apm
        
        # Significant drop in APM (< 50% of baseline)
        if apm_ratio < 0.5 and state.current_apm > 0:
            state.apm_degradation_count += 1
        else:
            state.apm_degradation_count = max(0, state.apm_degradation_count - 1)
    
    # Check activity pattern
    activity = input_monitor.get_activity_pattern()
    
    # Passive reading for extended period = potential fatigue
    if activity == 'passive' and state.activity_pattern == 'passive':
        state.fatigue_score = min(100, state.fatigue_score + 2)
    elif activity == 'active':
        state.fatigue_score = max(0, state.fatigue_score - 5)
    
    # APM degradation contributes to fatigue
    if state.apm_degradation_count > 3:
        state.fatigue_score = min(100, state.fatigue_score + 10)
        logger.warning(f"Cognitive fatigue detected (APM degradation). Score: {state.fatigue_score:.1f}")
    
    # Trigger soft reset if fatigue threshold exceeded
    try:
        fatigue_threshold = int(state.config.get("fatigue_threshold", 70))
    except Exception:
        fatigue_threshold = 70
    if state.fatigue_score > fatigue_threshold:
        logger.info(f"Fatigue threshold exceeded: {state.fatigue_score:.1f}")
        if soft_reset and not soft_reset.active:
            soft_reset.trigger()
            logger.info("🧘 Soft reset triggered")
        state.fatigue_score = 0  # Reset after intervention

def handle_resume():
    """User chose to WAIT FOR BREAK (Good Choice) - Close app/tab and grant rewards"""
    logger.info("User chose to WAIT FOR BREAK (Stamina Boost)")
    state.resilience_score += 5
    state.stamina_score += 10
    state.current_focus_score = min(100, state.current_focus_score + 5)
    
    # Clear distracting app tracking
    state.current_distracting_app = None
    state.distracting_start_time = None
    
    # If this was a browser tab, signal extension to close it
    # The extension will check for this status on next activity report
    if state.last_browser_url:
        # Store action for extension to pick up
        state.pending_close_tab = True
    
    # Async update XP
    if state.user:
        asyncio.create_task(update_user_xp(state.user.id, XP_RESUME_BONUS))

def handle_break(app_name: Optional[str] = None, url: Optional[str] = None):
    """User chose to OPEN ANYWAY (Bad Choice) - Allow access but track for gradual decay"""
    logger.info("User chose to OPEN ANYWAY (Resilience Hit)")
    # Instant penalty
    state.resilience_score = max(0, state.resilience_score - 10)
    state.current_focus_score = max(0, state.current_focus_score - 15)
    
    # Start tracking for gradual decay
    if app_name:
        state.current_distracting_app = app_name
    elif url:
        state.current_distracting_app = url
    else:
        state.current_distracting_app = state.active_window.get("title", "Unknown")
    
    state.distracting_start_time = datetime.now()
    state.last_decay_check = datetime.now()
    logger.info(f"Tracking gradual decay for: {state.current_distracting_app}")
    
    # Hide overlay immediately to allow access
    if blocker:
        blocker.hide()


# Initialize blocker now that handle_resume and handle_break are defined
try:
    blocker = FlowBlocker(
        on_resume=lambda: handle_resume(),
        on_break=lambda: handle_break()
    )
    logger.info("Flow blocker initialized")
except Exception as e:
    logger.warning(f"Blocker unavailable: {e}")
    blocker = None


def on_window_change(window_info):
    """Callback for window changes"""
    # Always update active window
    state.active_window = {
        "title": window_info["title"],
        "process": window_info["process_name"]
    }
    
    # Check for distractions (Layer 1)
    process_name = window_info["process_name"].lower()
    title = window_info["title"].lower()
    
    # Productive detection
    productive_keywords = state.config.get("productive_keywords", ["code", "visual studio", "docs"])
    is_productive = any(k in title for k in productive_keywords)
    
    # Distraction detection logic (Layer 1)
    distracting_keywords = state.config.get("distracting_keywords", ["netflix", "twitter", "facebook", "instagram", "reddit", "steam"])
    is_distraction = any(k in title for k in distracting_keywords)
    
    if not state.is_running:
        # Track Layer 1: Productive app usage
        if is_productive:
            if state.layer1_productive_start is None:
                state.layer1_productive_start = datetime.now()
                logger.info(f"Layer 1: Productive app detected - {window_info['title']}")
        else:
            # Reset if switching away from productive app
            if state.layer1_productive_start is not None:
                logger.info(f"Layer 1: Switched away from productive app. Resetting.")
                state.layer1_productive_start = None
        
        # Check tri-layer detection for auto-start
        # Use run_coroutine_threadsafe since we're in a thread
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(_check_and_auto_start_flow(), loop)
            else:
                # If no running loop, create a task in a new thread
                threading.Thread(target=lambda: asyncio.run(_check_and_auto_start_flow()), daemon=True).start()
        except RuntimeError:
            # No event loop in this thread, schedule in main thread
            try:
                # Try to get the main event loop
                loop = asyncio.get_running_loop()
                asyncio.run_coroutine_threadsafe(_check_and_auto_start_flow(), loop)
            except RuntimeError:
                # Fallback: run in a new thread with new event loop
                threading.Thread(target=lambda: asyncio.run(_check_and_auto_start_flow()), daemon=True).start()
        return
    
    # When flow is running, check for distractions and interventions
    # Blocked applications during flow
    blocked_apps = state.config.get("blocked_apps", [
        "valorant.exe", "league of legends.exe", "csgo.exe", "steam.exe", "discord.exe"
    ])
    if process_name in [app.lower() for app in blocked_apps]:
        trigger_intervention(f"Blocked application detected: {process_name}")
        return
    
    # Clear distracting app tracking if user switches to productive app
    if is_productive and state.current_distracting_app:
        logger.info(f"User switched to productive app: {window_info['title']}. Clearing decay tracking.")
        state.current_distracting_app = None
        state.distracting_start_time = None
        state.last_decay_check = None

    if is_distraction and state.is_running:
        trigger_intervention(
            f"Distraction detected: {window_info['title']}",
            app_name=window_info["process_name"]
        )

def trigger_intervention(reason: str, app_name: Optional[str] = None, url: Optional[str] = None):
    """Trigger the blocker overlay"""
    logger.warning(f"Intervention triggered: {reason}")
    state.distraction_count += 1
    
    # Show overlay with app name
    display_name = app_name or url or state.active_window.get("title", "Unknown")
    blocker.show(
        message=f"Focus breach detected: {display_name}. You are building resilience.",
        app_name=display_name
    )

# =============================
# System helpers (Windows DND)
# =============================
def _broadcast_settings_change():
    try:
        import ctypes
        HWND_BROADCAST = 0xFFFF
        WM_SETTINGCHANGE = 0x001A
        SMTO_ABORTIFHUNG = 0x0002
        ctypes.windll.user32.SendMessageTimeoutW(HWND_BROADCAST, WM_SETTINGCHANGE, 0, "UserPreferences", SMTO_ABORTIFHUNG, 200, None)
        logger.info("Broadcasted WM_SETTINGCHANGE (UserPreferences)")
    except Exception as e:
        logger.warning(f"Failed to broadcast setting change: {e}")

def enable_dnd():
    try:
        if platform.system() == 'Windows' and winreg:
            # Disable toast notifications
            notif_key = r"Software\\Microsoft\\Windows\\CurrentVersion\\Notifications\\Settings"
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, notif_key) as key:
                try:
                    prev, _ = winreg.QueryValueEx(key, "NOC_GLOBAL_SETTING_TOASTS_ENABLED")
                    state.dnd_prev_value = int(prev)
                except FileNotFoundError:
                    state.dnd_prev_value = None
                winreg.SetValueEx(key, "NOC_GLOBAL_SETTING_TOASTS_ENABLED", 0, winreg.REG_DWORD, 0)
            # Enable Focus Assist: 0=Off, 1=Priority only, 2=Alarms only
            qh_key = r"Software\\Microsoft\\Windows\\CurrentVersion\\QuietHours"
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, qh_key) as key:
                try:
                    prev_fa, _ = winreg.QueryValueEx(key, "FocusAssist")
                    state.focus_assist_prev_value = int(prev_fa)
                except FileNotFoundError:
                    state.focus_assist_prev_value = None
                winreg.SetValueEx(key, "FocusAssist", 0, winreg.REG_DWORD, 2)
            # Read-back verification
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, qh_key, 0, winreg.KEY_READ) as key:
                val, _ = winreg.QueryValueEx(key, "FocusAssist")
                if val == 2:
                    logger.info("[OK] Windows Focus Assist verified: 2 (Alarms only)")
                else:
                    logger.warning(f"[WARNING] Focus Assist verification failed. Expected 2, got {val}")
            
            # Verify toast setting
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, notif_key, 0, winreg.KEY_READ) as key:
                try:
                    toast_val, _ = winreg.QueryValueEx(key, "NOC_GLOBAL_SETTING_TOASTS_ENABLED")
                    if toast_val == 0:
                        logger.info("[OK] Toast notifications verified: disabled")
                    else:
                        logger.warning(f"[WARNING] Toast setting verification failed. Expected 0, got {toast_val}")
                except FileNotFoundError:
                    logger.warning("[WARNING] Could not verify toast setting")
            
            _broadcast_settings_change()
            
            # Method 2: Set additional notification registry keys
            try:
                # Disable banner notifications
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, notif_key) as key:
                    try:
                        winreg.SetValueEx(key, "NOC_GLOBAL_SETTING_BANNER_ENABLED", 0, winreg.REG_DWORD, 0)
                        logger.info("Banner notifications disabled")
                    except:
                        pass
                    try:
                        winreg.SetValueEx(key, "NOC_GLOBAL_SETTING_SOUND_ENABLED", 0, winreg.REG_DWORD, 0)
                        logger.info("Notification sounds disabled")
                    except:
                        pass
            except Exception as e:
                logger.warning(f"Additional notification settings failed: {e}")
            
            # Method 3: Use PowerShell to force enable Focus Assist and restart services
            try:
                import subprocess
                # Comprehensive PowerShell command
                ps_command = '''
                # Set registry
                $path = "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\QuietHours"
                Set-ItemProperty -Path $path -Name "FocusAssist" -Value 2 -Type DWord -Force
                
                # Disable all notification types
                $notifPath = "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Notifications\\Settings"
                Set-ItemProperty -Path $notifPath -Name "NOC_GLOBAL_SETTING_BANNER_ENABLED" -Value 0 -Type DWord -Force -ErrorAction SilentlyContinue
                Set-ItemProperty -Path $notifPath -Name "NOC_GLOBAL_SETTING_SOUND_ENABLED" -Value 0 -Type DWord -Force -ErrorAction SilentlyContinue
                
                # Restart notification-related processes
                $processes = @("ShellExperienceHost", "RuntimeBroker")
                foreach ($proc in $processes) {
                    try {
                        $procs = Get-Process -Name $proc -ErrorAction SilentlyContinue
                        if ($procs) {
                            $procs | Stop-Process -Force -ErrorAction SilentlyContinue
                            Start-Sleep -Milliseconds 500
                        }
                    } catch {}
                }
                
                # Broadcast settings change using Windows API
                $code = @'
                [DllImport("user32.dll", CharSet=CharSet.Auto)]
                public static extern IntPtr SendMessageTimeout(
                    IntPtr hWnd, uint Msg, IntPtr wParam, string lParam,
                    uint fuFlags, uint uTimeout, out IntPtr lpdwResult);
'@
                $type = Add-Type -MemberDefinition $code -Name User32 -Namespace Win32Functions -PassThru -ErrorAction SilentlyContinue
                if ($type) {
                    $HWND_BROADCAST = [IntPtr]0xffff
                    $WM_SETTINGCHANGE = 0x1a
                    $result = [IntPtr]::Zero
                    $type::SendMessageTimeout($HWND_BROADCAST, $WM_SETTINGCHANGE, [IntPtr]::Zero, "UserPreferences", 2, 5000, [ref]$result)
                }
                
                Write-Output "DND activation complete"
                '''
                result = subprocess.run(
                    ["powershell", "-ExecutionPolicy", "Bypass", "-Command", ps_command],
                    capture_output=True,
                    text=True,
                    timeout=15,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                if result.returncode == 0:
                    logger.info("[OK] Focus Assist enabled via PowerShell with service restart")
                    if result.stdout:
                        logger.debug(f"PowerShell output: {result.stdout.strip()}")
                else:
                    logger.warning(f"PowerShell command had issues: {result.stderr[:300] if result.stderr else 'Unknown error'}")
            except Exception as ps_error:
                logger.warning(f"PowerShell method failed (using registry only): {ps_error}")
            
            # Wait a moment for changes to take effect
            import time
            time.sleep(1)
            
            # Method 4: Open Windows Settings for manual verification/activation
            try:
                import subprocess
                subprocess.Popen(
                    ["ms-settings:quiethours"],
                    shell=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                logger.info("[ACTION REQUIRED] Windows Settings opened - Please verify Focus Assist is set to 'Alarms only'")
            except Exception as e:
                logger.warning(f"Could not open Windows Settings: {e}")
            
            logger.info("[OK] Windows DND registry values set successfully")
            logger.warning("[CRITICAL] Windows Focus Assist REQUIRES manual activation:")
            logger.warning("  1. Check the Windows Settings window that just opened")
            logger.warning("  2. In Focus Assist settings, toggle it to 'Alarms only' if it shows 'Off'")
            logger.warning("  3. Look for Focus Assist icon in Action Center (bottom-right)")
            logger.warning("  4. Some apps (Teams, Outlook, Discord) bypass Focus Assist - disable them individually")
            logger.warning("  5. Go to: Settings > System > Notifications to disable specific apps")
            return True
        else:
            logger.warning("DND not available on this platform")
            return False
    except Exception as e:
        logger.error(f"[ERROR] Failed to enable DND: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def disable_dnd():
    try:
        if platform.system() == 'Windows' and winreg:
            notif_key = r"Software\\Microsoft\\Windows\\CurrentVersion\\Notifications\\Settings"
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, notif_key) as key:
                value = 1 if state.dnd_prev_value is None else int(state.dnd_prev_value)
                winreg.SetValueEx(key, "NOC_GLOBAL_SETTING_TOASTS_ENABLED", 0, winreg.REG_DWORD, value)
            qh_key = r"Software\\Microsoft\\Windows\\CurrentVersion\\QuietHours"
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, qh_key) as key:
                value = 0 if state.focus_assist_prev_value is None else int(state.focus_assist_prev_value)
                winreg.SetValueEx(key, "FocusAssist", 0, winreg.REG_DWORD, value)
            _broadcast_settings_change()
            logger.info("Windows DND restored (toasts & Focus Assist)")
    except Exception as e:
        logger.error(f"Failed to disable DND: {e}")

# =============================
# Auto-start helper
# =============================
async def _auto_start_flow():
    if state.is_running:
        return
    state.is_running = True
    state.start_time = datetime.now()
    state.distraction_count = 0
    state.resilience_score = 0
    state.stamina_score = 0
    state.fatigue_score = 0
    state.baseline_apm = 0
    # Reset tri-layer detection state
    state.layer1_productive_start = None
    state.layer2_last_distraction = None
    state.active_streak_start = None
    # Create session in Supabase
    if state.user:
        state.current_session_id = await create_session(state.user.id)
    # Local DB
    if local_db:
        state.local_session_id = local_db.create_session(state.start_time)
        logger.info(f"Local session created: {state.local_session_id}")
    enable_dnd()
    logger.info("Flow session auto-started via tri-layer detection")

async def _check_and_auto_start_flow():
    """Check all three layers and auto-start flow if conditions are met"""
    if state.is_running:
        return
    
    now = datetime.now()
    
    # Check Layer 1: Productive app usage
    layer1_active = False
    if state.layer1_productive_start is not None:
        layer1_duration = (now - state.layer1_productive_start).total_seconds()
        layer1_active = layer1_duration >= state.flow_detection_threshold_seconds
        if layer1_active:
            logger.debug(f"Layer 1: Active (productive app for {layer1_duration:.0f}s)")
        else:
            logger.debug(f"Layer 1: Inactive (productive app for {layer1_duration:.0f}s, need {state.flow_detection_threshold_seconds}s)")
    else:
        logger.debug("Layer 1: Inactive (no productive app)")
    
    # Check Layer 2: No recent distractions
    layer2_active = False
    if state.layer2_last_distraction is None:
        layer2_active = True
        logger.debug("Layer 2: Active (no distractions)")
    else:
        distraction_age = (now - state.layer2_last_distraction).total_seconds()
        if distraction_age >= state.flow_detection_threshold_seconds:
            layer2_active = True
            logger.debug(f"Layer 2: Active (last distraction {distraction_age:.0f}s ago)")
        else:
            logger.debug(f"Layer 2: Inactive (distraction {distraction_age:.0f}s ago, need {state.flow_detection_threshold_seconds}s)")
    
    # Check Layer 3: Active input streak
    layer3_active = False
    if state.active_streak_start is not None:
        layer3_duration = (now - state.active_streak_start).total_seconds()
        layer3_active = layer3_duration >= state.flow_detection_threshold_seconds
        if layer3_active:
            logger.debug(f"Layer 3: Active (active input for {layer3_duration:.0f}s)")
        else:
            logger.debug(f"Layer 3: Inactive (active input for {layer3_duration:.0f}s, need {state.flow_detection_threshold_seconds}s)")
    else:
        logger.debug("Layer 3: Inactive (no active input streak)")
    
    # If all three layers are active, start flow
    if layer1_active and layer2_active and layer3_active:
        logger.info("All three layers active! Auto-starting flow session...")
        await _auto_start_flow()
    else:
        logger.debug(f"Tri-layer check: L1={layer1_active}, L2={layer2_active}, L3={layer3_active}")

# ============================================================================
# API MODELS
# ============================================================================

class BrowserActivity(BaseModel):
    url: str
    title: str
    timestamp: float

class QueryActivity(BaseModel):
    query: str
    engine: str
    timestamp: float

class FlowStatus(BaseModel):
    is_running: bool
    energy: float
    focus_score: float
    current_task: str
    session_duration: int
    resilience: int
    xp: int
    # Layer 3: Input monitoring
    apm: float
    activity_pattern: str
    fatigue_score: float

# ============================================================================
# FASTAPI APP
# ============================================================================

async def _track_resilience_decay():
    """Background task to track gradual resilience decay when user is in distracting app"""
    while True:
        try:
            await asyncio.sleep(60)  # Check every minute
            
            # Only track decay during active flow sessions
            if not state.is_running:
                continue
            
            # Check if user is currently in a distracting app/URL
            if state.current_distracting_app and state.distracting_start_time:
                # Calculate minutes spent in distracting content
                now = datetime.now()
                minutes_spent = (now - state.distracting_start_time).total_seconds() / 60
                
                # Apply decay: -1 resilience per minute
                if state.last_decay_check:
                    minutes_since_last_check = (now - state.last_decay_check).total_seconds() / 60
                    if minutes_since_last_check >= 1.0:
                        decay_amount = int(minutes_since_last_check)
                        state.resilience_score = max(0, state.resilience_score - decay_amount)
                        state.last_decay_check = now
                        if decay_amount > 0:
                            logger.info(f"Resilience decay: -{decay_amount} (Total time in {state.current_distracting_app}: {int(minutes_spent)} min)")
                else:
                    state.last_decay_check = now
        except Exception as e:
            logger.error(f"Error in resilience decay tracking: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Flow Engine...")
    
    # Initialize Database
    if not OFFLINE_MODE:
        init_supabase()
    
    # Get/Create User
    state.user = await get_or_create_user("Victus")  # Default user
    logger.info(f"User loaded: {state.user.name} (Level {state.user.level})")
    
    # Start Window Monitor
    window_monitor.callback = on_window_change
    window_monitor.start_monitoring()
    
    # Start Input Monitor (Layer 3)
    if input_monitor:
        input_monitor.start_monitoring()
        logger.info("Layer 3 (APM tracking) started")
    
    # Start resilience decay tracking
    decay_task = asyncio.create_task(_track_resilience_decay())
    
    yield
    
    # Shutdown
    logger.info("Shutting down Flow Engine...")
    decay_task.cancel()
    try:
        await decay_task
    except asyncio.CancelledError:
        pass
    window_monitor.stop_monitoring()
    if input_monitor:
        input_monitor.stop_monitoring()
    if blocker and blocker.active:
        blocker.hide()


app = FastAPI(title="Flow Engine API", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "online", "version": "1.0.0"}

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

@app.get("/api/test/dnd")
async def test_dnd():
    """Manually test DND activation"""
    logger.info("Manual DND test requested")
    result = enable_dnd()
    if result:
        return {
            "status": "success",
            "message": "DND enabled successfully. Check Windows Focus Assist settings to verify.",
            "dnd_prev_value": state.dnd_prev_value,
            "focus_assist_prev_value": state.focus_assist_prev_value
        }
    else:
        return {
            "status": "error",
            "message": "Failed to enable DND. Check logs for details."
        }

@app.post("/api/activity/browser")
async def record_browser_activity(activity: BrowserActivity):
    """Receive browser activity from Chrome Extension"""
    if not state.is_running:
        return {"status": "ignored"}
        
    state.last_browser_url = activity.url
    # Note: We can't get tab_id from the activity, but the extension tracks it
    
    # Check if we need to close tab (WAIT FOR BREAK was chosen)
    if state.pending_close_tab:
        state.pending_close_tab = False
        return {"status": "wait_for_break", "action": "close_tab"}
    
    # Layer 2: URL Detection
    distracting_urls = state.config.get("distracting_keywords", ["youtube.com/shorts", "twitter.com", "facebook.com", "instagram.com"])
    if any(d in activity.url for d in distracting_urls):
        trigger_intervention(f"Distracting URL: {activity.url}", url=activity.url)
        return {"status": "intervention_triggered", "action": "close_tab"}
        
    return {"status": "recorded"}

@app.post("/api/activity/query")
async def record_search_query(activity: QueryActivity):
    """Receive search query activity for AI analysis"""
    if not state.is_running:
        return {"status": "ignored"}

    q = activity.query.strip().lower()
    if not q:
        return {"status": "ignored"}

    # Quick fallback keyword check
    distracting_keywords = state.config.get("distracting_keywords", [
        "netflix", "twitter", "facebook", "instagram", "reddit", "tiktok", "shorts", "gaming"
    ])
    if any(k in q for k in distracting_keywords):
        trigger_intervention(f"Distracting query: {activity.query}", url=f"search:{activity.query}")
        return {"status": "intervention_triggered"}

    # AI-based classification (best-effort; classifier handles missing API keys)
    try:
        result = classifier.classify_url(f"https://search.local/?q={q}", context={
            "engine": activity.engine,
            "time": datetime.now().isoformat()
        })
        if result.get("classification") == "distracting":
            trigger_intervention(f"Distracting query (AI): {activity.query}", url=f"search:{activity.query}")
            return {"status": "intervention_triggered", "source": result.get("source")}
    except Exception as e:
        logger.error(f"Query AI classification error: {e}")

    return {"status": "recorded"}

@app.post("/api/start")
async def start_session():
    """Start a flow session"""
    if state.is_running:
        return {"status": "already_running"}
        
    state.is_running = True
    state.start_time = datetime.now()
    state.distraction_count = 0
    state.resilience_score = 0
    state.stamina_score = 0
    state.fatigue_score = 0
    state.baseline_apm = 0
    
    # Create session in Supabase
    if state.user:
        state.current_session_id = await create_session(state.user.id)
    
    # Create session in local DB for pattern learning
    if local_db:
        state.local_session_id = local_db.create_session(state.start_time)
        logger.info(f"Local session created: {state.local_session_id}")
    
    # Suppress notifications instead of DND (more reliable)
    if notification_suppressor:
        try:
            notification_suppressor.suppress_notifications()
            logger.info("🔕 Notifications suppressed for flow session")
        except Exception as e:
            logger.warning(f"Failed to suppress notifications: {e}")
    
    # Keep DND as fallback (though it requires manual activation)
    # enable_dnd()
    
    logger.info("Flow session started")
    return {"status": "started", "session_id": state.current_session_id}

@app.post("/api/stop")
async def stop_session():
    """Stop the current Flow Session"""
    if not state.is_running:
        return {"status": "not_running"}
        
    end_time = datetime.now()
    duration = int((end_time - state.start_time).total_seconds())
    
    # Calculate XP breakdown
    minutes = max(0, duration // 60)
    base_xp = minutes * XP_PER_MINUTE
    resilience_bonus = int(state.resilience_score)
    stamina_bonus = int(state.stamina_score)
    focus_bonus = int(max(0, state.current_focus_score) // 10)
    distraction_penalty = int(state.distraction_count * 0)
    xp_earned = base_xp + resilience_bonus + stamina_bonus + focus_bonus - distraction_penalty
    xp_breakdown = {
        "base": base_xp,
        "resilience": resilience_bonus,
        "stamina": stamina_bonus,
        "focus": focus_bonus,
        "penalty": distraction_penalty
    }
    
    # Update Supabase DB
    if state.current_session_id:
        await update_session(state.current_session_id, {
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "distraction_count": state.distraction_count,
            "resilience_score": state.resilience_score,
            "xp_earned": xp_earned
        })
        
    # Update User XP
    await update_user_xp(state.user.id, xp_earned)
    
    # Increment sessions count
    await increment_sessions_count(state.user.id)
    
    # Calculate cognitive profile after 3 sessions
    user_status = await get_user_status(state.user.id)
    if user_status["sessions_count"] == 3:
        # Get first 3 sessions for baseline calculation
        if local_db:
            first_three_sessions = local_db.get_recent_sessions(limit=3)
            if len(first_three_sessions) >= 3:
                # Calculate baseline cognitive profile
                avg_focus = sum(s.get('focus_score', 0) or 0 for s in first_three_sessions) / 3
                avg_duration = sum(s.get('duration_seconds', 0) or 0 for s in first_three_sessions) / 3
                avg_resilience = sum(s.get('resilience_score', 0) or 0 for s in first_three_sessions) / 3
                avg_distractions = sum(s.get('distraction_count', 0) or 0 for s in first_three_sessions) / 3
                
                # Calculate cognitive profile scores (0-100 scale)
                focus_score = max(0, min(100, avg_focus))
                stamina_score = max(0, min(100, (avg_duration / 3600) * 20))  # Normalize to 100
                resilience_score = max(0, min(100, avg_resilience))
                consistency_score = max(0, min(100, 100 - (avg_distractions * 10)))  # Lower distractions = higher consistency
                
                cognitive_profile = {
                    "focus": round(focus_score, 1),
                    "stamina": round(stamina_score, 1),
                    "resilience": round(resilience_score, 1),
                    "consistency": round(consistency_score, 1)
                }
                
                await update_cognitive_profile(state.user.id, cognitive_profile)
                logger.info(f"Cognitive profile calculated after 3 sessions: {cognitive_profile}")
    
    # Update cognitive profile on level up (after 3 sessions)
    elif user_status["sessions_count"] > 3 and state.user:
        # Check if user leveled up
        old_level = state.user.level
        new_level = (state.user.total_xp // 100) + 1
        if new_level > old_level:
            # Increase cognitive profile stats on level up
            if state.user.cognitive_profile:
                profile = state.user.cognitive_profile.copy()
                # Small increases per level
                profile["focus"] = min(100, profile.get("focus", 0) + 1)
                profile["stamina"] = min(100, profile.get("stamina", 0) + 1)
                profile["resilience"] = min(100, profile.get("resilience", 0) + 1)
                profile["consistency"] = min(100, profile.get("consistency", 0) + 0.5)
                await update_cognitive_profile(state.user.id, profile)
                logger.info(f"Cognitive profile updated on level up: {profile}")
    
    # Update local DB and analyze patterns
    if local_db and hasattr(state, 'local_session_id'):
        # Update session
        local_db.update_session(state.local_session_id, {
            'end_time': end_time,
            'duration_seconds': duration,
            'focus_score': state.current_focus_score,
            'fatigue_score': state.fatigue_score,
            'apm_average': state.current_apm,
            'distraction_count': state.distraction_count,
            'resilience_score': state.resilience_score,
            'stamina_score': state.stamina_score,
            'xp_total': xp_earned,
            'xp_breakdown': json.dumps(xp_breakdown)
        })
        
        # Log flow window (biological pattern)
        hour = state.start_time.hour
        flow_quality = (state.current_focus_score + (100 - state.fatigue_score)) / 2
        local_db.log_flow_window(
            state.start_time,
            hour,
            flow_quality,
            state.current_apm,
            duration // 60
        )
    
    # Restore notifications
    if notification_suppressor:
        try:
            notification_suppressor.restore_notifications()
            logger.info("🔔 Notifications restored after flow session")
        except Exception as e:
            logger.warning(f"Failed to restore notifications: {e}")
    
    # Mark session as stopped
    state.is_running = False
    logger.info(f"Flow session ended. Duration: {duration}s, XP earned: {xp_earned}")
    
    return {
        "status": "stopped",
        "duration": duration,
        "xp_earned": xp_earned,
        "xp_breakdown": xp_breakdown
    }


@app.get("/api/sessions/recent")
async def get_recent_sessions(limit: int = 10):
    if not local_db:
        return []
    sessions = local_db.get_recent_sessions(limit=limit)
    for s in sessions:
        # Parse xp breakdown if present
        xb = s.get('xp_breakdown')
        if isinstance(xb, str):
            try:
                s['xp_breakdown'] = json.loads(xb)
            except Exception:
                pass
    return sessions

@app.post("/api/soft_reset/trigger")
async def trigger_soft_reset():
    """Manually trigger the soft reset (for testing)"""
    if soft_reset:
        if not soft_reset.active:
            soft_reset.trigger()
            logger.info("🧘 Soft reset triggered via API")
            return {"status": "triggered"}
        else:
            return {"status": "already_active"}
    return {"status": "unavailable"}

@app.post("/api/penalty/forceful-termination")
async def apply_forceful_termination_penalty(penalty_amount: int = 15, reason: str = "Forcefully killed application"):
    """Apply resilience penalty when watchdog detects forceful app termination"""
    try:
        # Apply penalty to resilience score
        state.resilience_score = max(0, state.resilience_score - penalty_amount)
        logger.warning(f"⚠️  Resilience penalty applied: -{penalty_amount} points. Reason: {reason}")
        logger.warning(f"   New resilience score: {state.resilience_score}")
        
        # Also update user's stats if available
        if state.user and not OFFLINE_MODE:
            try:
                # Record the penalty in user stats
                supabase.table("user_stats").upsert({
                    "user_id": state.user.id,
                    "forceful_terminations": supabase.table("user_stats").select("forceful_terminations").eq("user_id", state.user.id).execute().data[0].get("forceful_terminations", 0) + 1 if supabase.table("user_stats").select("forceful_terminations").eq("user_id", state.user.id).execute().data else 1,
                    "last_penalty_date": datetime.now().isoformat()
                }).execute()
            except Exception as e:
                logger.error(f"Failed to record penalty in database: {e}")
        
        return {
            "status": "penalty_applied",
            "penalty_amount": penalty_amount,
            "new_resilience_score": state.resilience_score,
            "reason": reason
        }
    except Exception as e:
        logger.error(f"Failed to apply penalty: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/api/status")
async def get_status():
    """Get current flow status for dashboard"""
    duration = 0
    if state.is_running and state.start_time:
        duration = int((datetime.now() - state.start_time).total_seconds())
        
    # Simulate energy drain
    if state.is_running:
        state.energy_level = max(0, 100 - (duration / 60) * 0.5)  # Drains 0.5% per minute
    else:
        state.energy_level = min(100, state.energy_level + 1.0)  # Recovers 1% per request when idle
        
    return FlowStatus(
        is_running=state.is_running,
        energy=state.energy_level,
        focus_score=state.current_focus_score,
        current_task=state.active_window["title"],
        session_duration=duration,
        resilience=state.resilience_score,
        xp=state.user.total_xp if state.user else 0,
        apm=state.current_apm,
        activity_pattern=state.activity_pattern,
        fatigue_score=state.fatigue_score
    )

@app.get("/api/analytics/daily-xp")
async def get_daily_xp(days: int = 30):
    """Get XP gained per day for the last N days"""
    if not local_db:
        return []
    
    cursor = local_db.conn.cursor()
    cursor.execute("""
        SELECT 
            DATE(start_time) as date,
            SUM(xp_total) as total_xp
        FROM sessions
        WHERE start_time >= datetime('now', '-' || ? || ' days')
        AND xp_total IS NOT NULL
        GROUP BY DATE(start_time)
        ORDER BY date ASC
    """, (days,))
    
    results = []
    for row in cursor.fetchall():
        results.append({
            "date": row[0],
            "xp": row[1] or 0
        })
    
    return results

# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

class RegisterRequest(BaseModel):
    username: str
    password: str
    name: str

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/api/auth/register")
async def register_user(request: RegisterRequest):
    """Register a new user"""
    try:
        if not request.username or not request.password or not request.name:
            raise HTTPException(status_code=400, detail="Username, password, and name are required")
        
        if not db_module.supabase:
            raise HTTPException(status_code=500, detail="Database not connected. Please check Supabase configuration and ensure you've run the SQL schema.")
        
        user = await create_user_with_auth(request.username, request.password, request.name)
        
        if not user:
            raise HTTPException(status_code=400, detail="Username already exists")
        
        # Set user in state
        state.user = user
        
        return {
            "success": True,
            "user_id": user.id,
            "user": {
                "id": user.id,
                "name": user.name,
                "username": user.username,
                "level": user.level,
                "total_xp": user.total_xp
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Registration error: {e}")
        # Check if it's a database schema issue
        if "column" in error_msg.lower() or "does not exist" in error_msg.lower():
            raise HTTPException(
                status_code=500, 
                detail="Database schema error. Please run the SQL schema (supabase_complete_schema.sql) in your Supabase SQL Editor to add the required columns (username, password_hash, mission_log)."
            )
        raise HTTPException(status_code=500, detail=f"Registration failed: {error_msg}")

@app.post("/api/auth/login")
async def login_user(request: LoginRequest):
    """Authenticate a user"""
    if not request.username or not request.password:
        raise HTTPException(status_code=400, detail="Username and password are required")
    
    user = await authenticate_user(request.username, request.password)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Set user in state
    state.user = user
    
    return {
        "success": True,
        "user_id": user.id,
        "user": {
            "id": user.id,
            "name": user.name,
            "username": user.username,
            "level": user.level,
            "total_xp": user.total_xp
        }
    }

@app.post("/api/auth/restore")
async def restore_session(user_id: int = None):
    """Restore user session from user_id (called by frontend on load)"""
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    
    user = await get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Set user in state
    state.user = user
    
    return {
        "success": True,
        "user": {
            "id": user.id,
            "name": user.name,
            "username": user.username,
            "level": user.level,
            "total_xp": user.total_xp,
            "cognitive_profile": user.cognitive_profile,
            "sessions_count": user.sessions_count,
            "onboarding_complete": user.onboarding_complete
        }
    }

@app.get("/api/auth/me")
async def get_current_user():
    """Get current authenticated user"""
    if state.user:
        return {
            "success": True,
            "user": {
                "id": state.user.id,
                "name": state.user.name,
                "username": state.user.username,
                "level": state.user.level,
                "total_xp": state.user.total_xp,
                "cognitive_profile": state.user.cognitive_profile,
                "sessions_count": state.user.sessions_count,
                "onboarding_complete": state.user.onboarding_complete
            }
        }
    
    raise HTTPException(status_code=401, detail="Not authenticated")

@app.get("/api/user/status")
async def get_user_status_endpoint():
    """Get user status for onboarding check"""
    if not state.user:
        return {
            "is_new": True,
            "onboarding_complete": False,
            "sessions_count": 0
        }
    
    status = await get_user_status(state.user.id)
    # Fix: User is new if sessions_count == 0 AND onboarding_complete == False
    status["is_new"] = status["sessions_count"] == 0 and not status["onboarding_complete"]
    return status

@app.get("/api/user/profile")
async def get_user_profile():
    """Get user's cognitive profile and stats"""
    if not state.user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Get fresh user data from database
    user = await get_user_by_id(state.user.id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Return profile data
    cognitive_profile = user.cognitive_profile or {"focus": 0, "stamina": 0, "resilience": 0, "consistency": 0}
    
    # If user has less than 3 sessions, return zeros
    if user.sessions_count < 3:
        cognitive_profile = {"focus": 0, "stamina": 0, "resilience": 0, "consistency": 0}
    
    return {
        "level": user.level,
        "total_xp": user.total_xp,
        "sessions_count": user.sessions_count,
        "cognitive_profile": cognitive_profile,
        "onboarding_complete": user.onboarding_complete
    }

@app.get("/api/user/mission-log")
async def get_mission_log():
    """Get AI-generated mission log"""
    if not state.user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Get fresh user data from database
    user = await get_user_by_id(state.user.id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    mission_log = user.mission_log or {"goals": [], "focus_areas": []}
    return mission_log

class OnboardingRequest(BaseModel):
    timetable: Dict  # {start_time: str, end_time: str, work_days: List[str]}
    work_type: str  # e.g., "coding", "writing", "design"
    challenges: str  # Text description
    goals: str  # Text description

async def analyze_onboarding_with_ai(onboarding_data: OnboardingRequest) -> Dict:
    """Use Groq API to analyze onboarding responses and generate personalized schedule"""
    import requests
    
    api_key = os.getenv("AI_API_KEY") or os.getenv("GROQ_API_KEY", "")
    if not api_key:
        logger.warning("AI API key not configured. Returning default schedule.")
        return {
            "schedule": {
                "predicted_flow_windows": ["09:00-11:00", "14:00-16:00"],
                "baseline_focus_duration": 25
            },
            "mission_log": {
                "goals": onboarding_data.goals.split("\n") if onboarding_data.goals else [],
                "focus_areas": [onboarding_data.work_type]
            },
            "app_suggestions": {
                "productive": ["vscode", "terminal", "browser"],
                "distracting": ["discord", "steam", "social media"]
            }
        }
    
    prompt = f"""Analyze this user's onboarding information and create a personalized productivity schedule.

User Information:
- Work Type: {onboarding_data.work_type}
- Daily Timetable: {json.dumps(onboarding_data.timetable)}
- Challenges: {onboarding_data.challenges}
- Goals: {onboarding_data.goals}

Generate:
1. Predicted flow windows (times when user is most likely to enter flow state)
2. Recommended baseline focus duration (in minutes)
3. Initial mission log with goals and focus areas
4. Productive and distracting app suggestions based on work type

Respond in JSON format:
{{
    "schedule": {{
        "predicted_flow_windows": ["HH:MM-HH:MM", ...],
        "baseline_focus_duration": 25
    }},
    "mission_log": {{
        "goals": ["goal1", "goal2", ...],
        "focus_areas": ["area1", "area2", ...]
    }},
    "app_suggestions": {{
        "productive": ["app1", "app2", ...],
        "distracting": ["app1", "app2", ...]
    }}
}}"""
    
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a productivity coach that analyzes user information and creates personalized schedules. Always respond in valid JSON format."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        
        result = response.json()
        content = result['choices'][0]['message']['content']
        
        # Parse JSON from response
        analysis = json.loads(content)
        return analysis
        
    except Exception as e:
        logger.error(f"AI onboarding analysis failed: {e}")
        # Return default schedule
        return {
            "schedule": {
                "predicted_flow_windows": ["09:00-11:00", "14:00-16:00"],
                "baseline_focus_duration": 25
            },
            "mission_log": {
                "goals": onboarding_data.goals.split("\n") if onboarding_data.goals else [],
                "focus_areas": [onboarding_data.work_type]
            },
            "app_suggestions": {
                "productive": ["vscode", "terminal", "browser"],
                "distracting": ["discord", "steam", "social media"]
            }
        }

@app.post("/api/onboarding/submit")
async def submit_onboarding(onboarding_data: OnboardingRequest):
    """Submit onboarding responses"""
    if not state.user:
        raise HTTPException(status_code=400, detail="User not found")
    
    # Store onboarding data
    await update_onboarding_data(state.user.id, onboarding_data.dict())
    
    # Analyze with AI
    analysis = await analyze_onboarding_with_ai(onboarding_data)
    
    # Store mission_log from AI analysis
    if analysis.get("mission_log"):
        await update_mission_log(state.user.id, analysis["mission_log"])
        # Also update state.user for immediate access
        if state.user:
            state.user.mission_log = analysis["mission_log"]
    
    # Update user config with AI suggestions
    if analysis.get("schedule"):
        schedule = analysis["schedule"]
        if "predicted_flow_windows" in schedule:
            state.config["flow_windows"] = schedule["predicted_flow_windows"]
        if "baseline_focus_duration" in schedule:
            state.config["baseline_focus_minutes"] = schedule["baseline_focus_duration"]
            await update_baseline(state.user.id, schedule["baseline_focus_duration"])
    
    if analysis.get("app_suggestions"):
        suggestions = analysis["app_suggestions"]
        if "productive" in suggestions:
            state.config["productive_keywords"] = suggestions["productive"]
        if "distracting" in suggestions:
            state.config["distracting_keywords"] = suggestions["distracting"]
    
    # Save config
    with open(CONFIG_FILE, "w") as f:
        json.dump(state.config, f, indent=2)
    
    return {
        "status": "success",
        "analysis": analysis
    }

@app.get("/api/analytics/flow-time")
async def get_flow_time(days: int = 30):
    """Get flow state time per day based on tri-layer detection"""
    if not local_db:
        return []
    
    cursor = local_db.conn.cursor()
    # Flow time is determined by sessions where all three layers were active
    # We'll use sessions with high focus_score and low distraction_count as proxy
    cursor.execute("""
        SELECT 
            DATE(start_time) as date,
            SUM(duration_seconds) / 60.0 as flow_minutes,
            COUNT(*) as flow_sessions
        FROM sessions
        WHERE start_time >= datetime('now', '-' || ? || ' days')
        AND duration_seconds > 0
        AND (focus_score IS NULL OR focus_score >= 70)
        AND (distraction_count IS NULL OR distraction_count <= 2)
        GROUP BY DATE(start_time)
        ORDER BY date ASC
    """, (days,))
    
    results = []
    for row in cursor.fetchall():
        results.append({
            "date": row[0],
            "flow_minutes": round(row[1] or 0, 1),
            "sessions": row[2] or 0
        })
    
    return results

@app.get("/api/insights/flow-analysis")
async def get_flow_insights():
    """Get AI-powered insights about flow state, improvements, and flow breakers"""
    if not local_db or not pattern_analyzer:
        return {
            "how_to_improve": ["Enable pattern learning to get personalized insights"],
            "improvements_needed": [],
            "improvement_progress": {},
            "flow_breakers": []
        }
    
    try:
        # Get recent sessions for analysis
        recent_sessions = local_db.get_recent_sessions(limit=20)
        
        # Analyze patterns
        app_patterns = pattern_analyzer.analyze_app_patterns()
        bio_patterns = pattern_analyzer.detect_biological_patterns(days=30)
        
        # Calculate improvement metrics
        if len(recent_sessions) >= 3:
            first_three = recent_sessions[-3:]
            last_three = recent_sessions[:3]
            
            avg_focus_early = sum(s.get('focus_score', 0) or 0 for s in first_three) / len(first_three)
            avg_focus_late = sum(s.get('focus_score', 0) or 0 for s in last_three) / len(last_three)
            
            avg_duration_early = sum(s.get('duration_seconds', 0) or 0 for s in first_three) / len(first_three)
            avg_duration_late = sum(s.get('duration_seconds', 0) or 0 for s in last_three) / len(last_three)
            
            improvement_progress = {
                "focus_improvement": round(avg_focus_late - avg_focus_early, 1),
                "duration_improvement": round((avg_duration_late - avg_duration_early) / 60, 1),
                "sessions_completed": len(recent_sessions)
            }
        else:
            improvement_progress = {
                "focus_improvement": 0,
                "duration_improvement": 0,
                "sessions_completed": len(recent_sessions)
            }
        
        # Identify flow breakers
        flow_breakers = []
        frequent_distractions = app_patterns.get('frequent_distractions', [])
        for app in frequent_distractions[:5]:  # Top 5
            flow_breakers.append({
                "app": app['app_name'],
                "breaks": app['flow_breaks'],
                "recommendation": f"Consider blocking {app['app_name']} during flow sessions"
            })
        
        # Generate AI insights using classifier
        insights = []
        improvements_needed = []
        
        # Analyze current performance
        if recent_sessions:
            latest = recent_sessions[0]
            avg_distractions = sum(s.get('distraction_count', 0) or 0 for s in recent_sessions[:5]) / min(5, len(recent_sessions))
            avg_focus = sum(s.get('focus_score', 0) or 0 for s in recent_sessions[:5]) / min(5, len(recent_sessions))
            
            if avg_distractions > 3:
                improvements_needed.append("Reduce distractions - currently averaging " + str(round(avg_distractions, 1)) + " per session")
                insights.append("Focus on one task at a time. Close unnecessary tabs and apps before starting.")
            
            if avg_focus < 70:
                improvements_needed.append("Improve focus score - currently at " + str(round(avg_focus, 1)) + "%")
                insights.append("Try working in shorter, more focused sessions. Take breaks between deep work periods.")
            
            if bio_patterns.get('peak_hours'):
                insights.append(f"Your peak flow hours are {', '.join(map(str, bio_patterns['peak_hours']))}. Schedule important work during these times.")
            else:
                insights.append("Track your sessions for 3+ days to identify your biological flow windows.")
        
        # Use AI classifier for additional insights if available
        if classifier and not classifier.use_fallback:
            try:
                # Generate AI insight prompt
                avg_focus = sum(s.get('focus_score', 0) or 0 for s in recent_sessions[:5]) / min(5, len(recent_sessions)) if recent_sessions else 0
                distractor_names = [a['app_name'] for a in frequent_distractions[:3]]
                peak_hours_str = ', '.join(map(str, bio_patterns.get('peak_hours', []))) if bio_patterns.get('peak_hours') else 'Not yet identified'
                
                prompt = f"""Based on this user's flow data:
- Recent sessions: {len(recent_sessions)}
- Average focus: {avg_focus:.1f}%
- Frequent distractions: {distractor_names if distractor_names else 'None identified'}
- Peak hours: {peak_hours_str}

Provide 2-3 actionable insights on how to improve flow state. Be specific and practical. Respond in JSON format with a 'reasoning' field containing the insights as a single string."""
                
                result = classifier._call_ai_api(prompt)
                ai_insights = classifier._parse_ai_response(result)
                if ai_insights.get('reasoning'):
                    # Split reasoning into multiple insights if it contains multiple sentences
                    reasoning = ai_insights['reasoning']
                    if '. ' in reasoning:
                        insights.extend([s.strip() for s in reasoning.split('. ') if s.strip()])
                    else:
                        insights.append(reasoning)
            except Exception as e:
                logger.warning(f"AI insight generation failed: {e}")
        
        # Default insights if none generated
        if not insights:
            insights = [
                "Maintain consistent work schedule to build flow habits",
                "Minimize context switching by closing distracting apps",
                "Take regular breaks to prevent cognitive fatigue"
            ]
        
        return {
            "how_to_improve": insights,
            "improvements_needed": improvements_needed,
            "improvement_progress": improvement_progress,
            "flow_breakers": flow_breakers
        }
        
    except Exception as e:
        logger.error(f"Error generating insights: {e}")
        return {
            "how_to_improve": ["Error generating insights. Please try again later."],
            "improvements_needed": [],
            "improvement_progress": {},
            "flow_breakers": []
        }

    # Mount static files from frontend build
    # This serves the React app
    frontend_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend-react", "dist")
    if os.path.exists(frontend_dist):
        app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")
        
        @app.get("/{full_path:path}")
        async def serve_frontend(full_path: str):
            # Check if file exists in dist
            file_path = os.path.join(frontend_dist, full_path)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                return FileResponse(file_path)
            # Otherwise return index.html for SPA routing
            return FileResponse(os.path.join(frontend_dist, "index.html"))
    else:
        logger.warning(f"Frontend dist directory not found at {frontend_dist}")

def start_server():
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)

if __name__ == "__main__":
    start_server()

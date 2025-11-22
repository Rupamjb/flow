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
    get_recent_sessions, update_user_xp, Session, User
)
from window_monitor import WindowMonitor
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

state = FlowState()

# Load Config
CONFIG_FILE = "user_config.json"
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                state.config = json.load(f)
                logger.info("User configuration loaded.")
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
blocker = FlowBlocker(
    on_resume=lambda: handle_resume(),
    on_break=lambda: handle_break()
)

# Initialize input monitor if available
input_monitor = None
if INPUT_MONITOR_AVAILABLE:
    def on_input_update(data):
        state.current_apm = data['apm']
        state.activity_pattern = 'active' if data['keyboard_events'] > 30 else 'passive'
        # Track continuous active streak
        now = datetime.now()
        if state.activity_pattern == 'active':
            if state.active_streak_start is None:
                state.active_streak_start = now
            else:
                # If active > 4 minutes and not running, auto-start flow
                threshold = int(state.config.get("auto_flow_active_seconds", 240))
                if not state.is_running and (now - state.active_streak_start).total_seconds() >= threshold:
                    logger.info("Auto-starting flow based on active input streak (4 min)")
                    asyncio.create_task(_auto_start_flow())
        else:
            state.active_streak_start = None

        # Call fatigue detection on each input update
        detect_cognitive_fatigue()
    
    input_monitor = InputMonitor(callback=on_input_update)
    logger.info("Input monitor initialized (Layer 3 active)")

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
    """User chose to WAIT FOR BREAK (Good Choice)"""
    logger.info("User chose to WAIT (Stamina Boost)")
    state.resilience_score += 5
    state.stamina_score += 10
    state.current_focus_score = min(100, state.current_focus_score + 5)
    
    # Async update XP
    asyncio.create_task(update_user_xp(state.user.id, XP_RESUME_BONUS))

def handle_break():
    """User chose to OPEN ANYWAY (Bad Choice)"""
    logger.info("User chose to OPEN ANYWAY (Resilience Hit)")
    state.resilience_score = max(0, state.resilience_score - 10)
    state.current_focus_score = max(0, state.current_focus_score - 15)
    
    # Allow the distraction for a short period? 
    # For now, we just log the penalty.
    # In a full implementation, we would whitelist the current window/url for X minutes.

def on_window_change(window_info):
    """Callback for window changes"""
    if not state.is_running:
        return
        
    state.active_window = {
        "title": window_info["title"],
        "process": window_info["process_name"]
    }
    
    # Check for distractions (Layer 1)
    process_name = window_info["process_name"].lower()
    title = window_info["title"].lower()
    
    # Blocked applications during flow
    blocked_apps = state.config.get("blocked_apps", [
        "valorant.exe", "league of legends.exe", "csgo.exe", "steam.exe", "discord.exe"
    ])
    if process_name in [app.lower() for app in blocked_apps]:
        trigger_intervention(f"Blocked application detected: {process_name}")
        return

    # Distraction detection logic (Layer 1)
    distracting_keywords = state.config.get("distracting_keywords", ["netflix", "twitter", "facebook", "instagram", "reddit", "steam"])
    is_distraction = any(k in title for k in distracting_keywords)
    
    # Productive detection
    productive_keywords = state.config.get("productive_keywords", ["code", "visual studio", "docs"])
    is_productive = any(k in title for k in productive_keywords)
    
    if is_productive and not state.is_running:
        # Auto-start flow if productive for > 3 minutes (Simulated here)
        # In real impl, we'd track time_spent_productive
        pass

    if is_distraction and state.is_running:
        trigger_intervention(f"Distraction detected: {window_info['title']}")

def trigger_intervention(reason: str):
    """Trigger the blocker overlay"""
    logger.warning(f"Intervention triggered: {reason}")
    state.distraction_count += 1
    
    # Show overlay
    blocker.show(message=f"Focus breach detected. You are building resilience.")

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
                logger.info(f"Windows Focus Assist set to {val}")
            _broadcast_settings_change()
            logger.info("Windows DND enabled (toasts disabled, Focus Assist=Alarms only)")
    except Exception as e:
        logger.error(f"Failed to enable DND: {e}")

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
    # Create session in Supabase
    if state.user:
        state.current_session_id = await create_session(state.user.id)
    # Local DB
    if local_db:
        state.local_session_id = local_db.create_session(state.start_time)
        logger.info(f"Local session created: {state.local_session_id}")
    enable_dnd()
    logger.info("Flow session auto-started")

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
    
    yield
    
    # Shutdown
    logger.info("Shutting down Flow Engine...")
    window_monitor.stop_monitoring()
    if input_monitor:
        input_monitor.stop_monitoring()
    if blocker.active:
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

@app.post("/api/activity/browser")
async def record_browser_activity(activity: BrowserActivity):
    """Receive browser activity from Chrome Extension"""
    if not state.is_running:
        return {"status": "ignored"}
        
    state.last_browser_url = activity.url
    
    # Layer 2: URL Detection
    distracting_urls = state.config.get("distracting_keywords", ["youtube.com/shorts", "twitter.com", "facebook.com", "instagram.com"])
    if any(d in activity.url for d in distracting_urls):
        trigger_intervention(f"Distracting URL: {activity.url}")
        return {"status": "intervention_triggered"}
        
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
        trigger_intervention(f"Distracting query: {activity.query}")
        return {"status": "intervention_triggered"}

    # AI-based classification (best-effort; classifier handles missing API keys)
    try:
        result = classifier.classify_url(f"https://search.local/?q={q}", context={
            "engine": activity.engine,
            "time": datetime.now().isoformat()
        })
        if result.get("classification") == "distracting":
            trigger_intervention(f"Distracting query (AI): {activity.query}")
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
    
    enable_dnd()
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

def start_server():
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)

if __name__ == "__main__":
    start_server()

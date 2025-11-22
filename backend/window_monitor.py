"""
Flow State Facilitator - Window Monitor
Windows API integration for tracking active windows and creating overlay blocks.
"""

import time
import threading
from typing import Optional, Callable

try:
    import win32gui
    import win32process
    import win32con
    import psutil
    WINDOWS_AVAILABLE = True
except ImportError:
    WINDOWS_AVAILABLE = False
    print("⚠️  pywin32 not available. Window monitoring disabled.")

class WindowMonitor:
    """Monitor active windows using Win32 API"""
    
    def __init__(self, callback: Optional[Callable] = None):
        if not WINDOWS_AVAILABLE:
            raise RuntimeError("pywin32 is required for window monitoring on Windows")
        
        self.callback = callback
        self.monitoring = False
        self.monitor_thread = None
        self.current_window = None
        self.current_process = None
        
    def get_active_window_info(self) -> dict:
        """Get information about the currently active window"""
        try:
            hwnd = win32gui.GetForegroundWindow()
            if hwnd == 0:
                return None
            
            # Get window title
            window_title = win32gui.GetWindowText(hwnd)
            
            # Get process info
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            
            try:
                process = psutil.Process(pid)
                process_name = process.name()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                process_name = "Unknown"
            
            return {
                "hwnd": hwnd,
                "title": window_title,
                "process_name": process_name,
                "pid": pid
            }
            
        except Exception as e:
            print(f"Error getting active window: {e}")
            return None
    
    def start_monitoring(self, interval: float = 2.0):
        """Start monitoring active window in background thread"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval,), daemon=True)
        self.monitor_thread.start()
        print("🔍 Window monitoring started")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        print("🛑 Window monitoring stopped")
    
    def _monitor_loop(self, interval: float):
        """Background monitoring loop"""
        while self.monitoring:
            try:
                window_info = self.get_active_window_info()
                
                if window_info:
                    # Check if window changed
                    if (not self.current_window or 
                        window_info["title"] != self.current_window.get("title")):
                        
                        self.current_window = window_info
                        self.current_process = window_info["process_name"]
                        
                        # Call callback if provided
                        if self.callback:
                            self.callback(window_info)
                
                time.sleep(interval)
                
            except Exception as e:
                print(f"Error in monitor loop: {e}")
                time.sleep(interval)


class OverlayWindow:
    """Create a full-screen overlay window to block distractions"""
    
    def __init__(self):
        if not WINDOWS_AVAILABLE:
            raise RuntimeError("pywin32 is required for overlay windows")
        
        self.hwnd = None
        self.visible = False
    
    def show_overlay(self, message: str = "You are in Flow. Break it?", countdown: int = 10):
        """Show blocking overlay (simplified version for hackathon)"""
        # For hackathon: just print to console
        # In production: create actual topmost window with Tkinter or Win32 API
        print("=" * 60)
        print(f"🚫 OVERLAY TRIGGERED: {message}")
        print(f"⏱️  Countdown: {countdown} seconds")
        print("=" * 60)
        
        # TODO: Implement actual overlay window
        # This would use win32gui.CreateWindow with WS_EX_TOPMOST style
        # Or use Tkinter with .attributes('-topmost', True)
        
        self.visible = True
        return True
    
    def hide_overlay(self):
        """Hide the overlay"""
        if self.visible:
            print("✅ Overlay hidden")
            self.visible = False


# Standalone test
if __name__ == "__main__":
    if not WINDOWS_AVAILABLE:
        print("❌ This module requires pywin32. Install with: pip install pywin32")
        exit(1)
    
    def on_window_change(window_info):
        print(f"🪟 Active Window: {window_info['title']} ({window_info['process_name']})")
    
    monitor = WindowMonitor(callback=on_window_change)
    monitor.start_monitoring(interval=3.0)
    
    print("Monitoring active windows. Press Ctrl+C to stop...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        monitor.stop_monitoring()
        print("\n👋 Monitoring stopped")

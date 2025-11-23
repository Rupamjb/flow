"""
Flow State Facilitator - Watchdog Process
Monitors the main server and applies penalties if forcefully killed.
Does NOT automatically restart - user must restart manually.
"""

import os
import sys
import time
import psutil
import requests
from pathlib import Path
from datetime import datetime

class Watchdog:
    def __init__(self):
        self.main_script = Path(__file__).parent / "main.py"
        self.main_process = None
        self.heartbeat_interval = 10  # seconds
        self.last_health_check = None
        self.was_healthy_before_death = False
        
    def log(self, message: str):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] 🐕 WATCHDOG: {message}")
    
    def is_process_running(self, pid: int) -> bool:
        """Check if a process is running by PID"""
        try:
            process = psutil.Process(pid)
            return process.is_running() and process.status() != psutil.STATUS_ZOMBIE
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
    
    def find_main_process(self):
        """Find the main.py process if it's already running"""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info['cmdline']
                if cmdline and 'python' in cmdline[0].lower() and 'main.py' in ' '.join(cmdline):
                    return proc
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return None
    
    def apply_resilience_penalty(self):
        """Apply resilience penalty for forcefully killing the app"""
        try:
            self.log("⚠️  Applying resilience penalty for forceful termination...")
            response = requests.post(
                "http://127.0.0.1:8000/api/penalty/forceful-termination",
                json={"penalty_amount": 15, "reason": "Forcefully killed application"},
                timeout=5.0
            )
            if response.status_code == 200:
                self.log("✅ Resilience penalty applied (-15 points)")
            else:
                self.log(f"⚠️  Failed to apply penalty: {response.status_code}")
        except Exception as e:
            self.log(f"⚠️  Could not apply penalty (backend may be down): {e}")
    
    def check_health(self) -> bool:
        """Check if main server is healthy via HTTP health endpoint"""
        try:
            response = requests.get("http://127.0.0.1:8000/api/health", timeout=5.0)
            return response.status_code == 200
        except Exception:
            return False
    
    def monitor(self):
        """Main monitoring loop - monitors only, does not restart"""
        self.log("🚀 Watchdog started (monitoring only - no auto-restart)")
        
        # Find the main server process
        existing_process = self.find_main_process()
        if existing_process:
            self.log(f"Found main server (PID: {existing_process.pid})")
            self.main_process = existing_process
        else:
            self.log("⚠️  Main server not found. Please start it manually.")
            self.log("   Waiting for main server to start...")
            # Wait for user to start the server
            while True:
                time.sleep(5)
                existing_process = self.find_main_process()
                if existing_process:
                    self.log(f"✅ Main server detected (PID: {existing_process.pid})")
                    self.main_process = existing_process
                    break
        
        # Monitoring loop
        while True:
            try:
                time.sleep(self.heartbeat_interval)
                
                # Check if process is still running
                if self.main_process and self.is_process_running(self.main_process.pid):
                    # Process exists, check health
                    if self.check_health():
                        self.log(f"✅ Heartbeat OK (PID: {self.main_process.pid})")
                        self.was_healthy_before_death = True
                        self.last_health_check = datetime.now()
                    else:
                        self.log(f"⚠️  Process running but health check failed")
                        self.was_healthy_before_death = False
                else:
                    # Process died
                    self.log("💀 Main server process died!")
                    
                    # Check if it was a forceful kill (was healthy before death)
                    if self.was_healthy_before_death:
                        self.log("🚨 Detected forceful termination (app was healthy before death)")
                        # Wait a moment for backend to potentially come back
                        time.sleep(3)
                        # Try to apply penalty
                        self.apply_resilience_penalty()
                    
                    # Do NOT restart - just log and wait for manual restart
                    self.log("⚠️  Watchdog will NOT auto-restart. Please restart the server manually.")
                    self.log("   Waiting for manual restart...")
                    
                    # Wait for user to restart
                    self.main_process = None
                    self.was_healthy_before_death = False
                    
                    while True:
                        time.sleep(5)
                        existing_process = self.find_main_process()
                        if existing_process:
                            self.log(f"✅ Main server restarted manually (PID: {existing_process.pid})")
                            self.main_process = existing_process
                            break
                
            except KeyboardInterrupt:
                self.log("⚠️  Received interrupt signal. Shutting down...")
                break
            
            except Exception as e:
                self.log(f"❌ Error in monitoring loop: {e}")
                time.sleep(5)

if __name__ == "__main__":
    print("=" * 60)
    print("🐕 Flow State Facilitator - Watchdog Monitor")
    print("   (Monitoring Only - No Auto-Restart)")
    print("=" * 60)
    
    watchdog = Watchdog()
    watchdog.monitor()

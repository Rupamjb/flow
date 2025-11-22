"""
Flow State Facilitator - Watchdog Process
Monitors the main server and restarts it if it crashes or is killed.
Implements mutual recovery: main.py can also restart this watchdog.
"""

import os
import sys
import time
import psutil
import subprocess
from pathlib import Path
from datetime import datetime

class Watchdog:
    def __init__(self):
        self.main_script = Path(__file__).parent / "main.py"
        self.main_process = None
        self.restart_count = 0
        self.max_restart_attempts = 10
        self.restart_delay = 5  # seconds
        self.heartbeat_interval = 10  # seconds
        
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
    
    def start_main_server(self):
        """Start the main FastAPI server"""
        self.log(f"Starting main server: {self.main_script}")
        
        try:
            # Start the server as a subprocess
            process = subprocess.Popen(
                [sys.executable, str(self.main_script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
            )
            
            self.main_process = psutil.Process(process.pid)
            self.log(f"✅ Main server started with PID: {process.pid}")
            return True
            
        except Exception as e:
            self.log(f"❌ Failed to start main server: {e}")
            return False
    
    def check_health(self) -> bool:
        """Check if main server is healthy via HTTP health endpoint"""
        try:
            import httpx
            response = httpx.get("http://127.0.0.1:8000/api/health", timeout=5.0)
            return response.status_code == 200
        except Exception:
            return False
    
    def monitor(self):
        """Main monitoring loop"""
        self.log("🚀 Watchdog started")
        
        # Check if main server is already running
        existing_process = self.find_main_process()
        if existing_process:
            self.log(f"Found existing main server (PID: {existing_process.pid})")
            self.main_process = existing_process
        else:
            # Start the main server
            if not self.start_main_server():
                self.log("❌ Failed to start main server on first attempt")
                return
        
        # Monitoring loop
        while True:
            try:
                time.sleep(self.heartbeat_interval)
                
                # Check if process is still running
                if self.main_process and self.is_process_running(self.main_process.pid):
                    # Process exists, check health
                    if self.check_health():
                        self.log(f"✅ Heartbeat OK (PID: {self.main_process.pid})")
                    else:
                        self.log(f"⚠️  Process running but health check failed")
                else:
                    # Process died
                    self.log("💀 Main server process died!")
                    
                    if self.restart_count >= self.max_restart_attempts:
                        self.log(f"❌ Max restart attempts ({self.max_restart_attempts}) reached. Giving up.")
                        break
                    
                    self.restart_count += 1
                    self.log(f"🔄 Attempting restart #{self.restart_count}...")
                    
                    time.sleep(self.restart_delay)
                    
                    if self.start_main_server():
                        self.log("✅ Successfully restarted main server")
                        # Reset counter on successful restart
                        time.sleep(30)  # Wait 30s to see if it stays up
                        if self.check_health():
                            self.restart_count = 0
                    else:
                        self.log("❌ Failed to restart main server")
                
            except KeyboardInterrupt:
                self.log("⚠️  Received interrupt signal. Shutting down...")
                if self.main_process and self.is_process_running(self.main_process.pid):
                    self.log("Terminating main server...")
                    self.main_process.terminate()
                    self.main_process.wait(timeout=10)
                break
            
            except Exception as e:
                self.log(f"❌ Error in monitoring loop: {e}")
                time.sleep(5)

if __name__ == "__main__":
    print("=" * 60)
    print("🐕 Flow State Facilitator - Watchdog Monitor")
    print("=" * 60)
    
    watchdog = Watchdog()
    watchdog.monitor()

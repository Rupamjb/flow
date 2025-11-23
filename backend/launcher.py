"""
Flow State Facilitator - Main Launcher
The central GUI entry point for the application.
Manages the backend process, onboarding, and system tray integration.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
import os
import threading
import webbrowser
from pathlib import Path
from PIL import Image

# Import local modules
try:
    import pystray
    from pystray import MenuItem as item
except ImportError:
    pystray = None

# Paths
BACKEND_DIR = Path(__file__).parent
MAIN_SCRIPT = BACKEND_DIR / "main.py"
ICON_PATH = BACKEND_DIR.parent / "extension" / "icon48.png"
CONFIG_FILE = BACKEND_DIR.parent / "user_config.json"

class FlowLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("The Flow Engine")
        self.root.geometry("400x500")
        self.root.configure(bg="#0a0a0a")
        self.root.resizable(False, False)
        
        # State
        self.server_process = None
        self.is_running = False
        self.tray_icon = None
        
        # Styles
        self._setup_styles()
        
        # UI
        self._create_ui()
        
        # Protocol handlers
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Auto-start check
        self._check_config()

    def _check_config(self):
        """Check if config exists and auto-start if needed"""
        if CONFIG_FILE.exists():
            # Could load config here to check for auto-start preference
            pass
        else:
            # First time run?
            pass

    def _setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Colors
        self.colors = {
            "bg": "#0a0a0a",
            "fg": "#ffffff",
            "accent": "#219ebc",
            "warning": "#ffb703",
            "danger": "#d00000",
            "success": "#2a9d8f",
            "panel": "#1a1a1a"
        }
        
        self.style.configure("TFrame", background=self.colors["bg"])
        self.style.configure("TLabel", background=self.colors["bg"], foreground=self.colors["fg"], font=("Segoe UI", 10))
        self.style.configure("Header.TLabel", font=("Segoe UI", 18, "bold"), foreground=self.colors["accent"])
        self.style.configure("Status.TLabel", font=("Consolas", 12))

    def _create_ui(self):
        # Main Container
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill="x", pady=(0, 30))
        
        ttk.Label(header_frame, text="FLOW ENGINE", style="Header.TLabel").pack(side="top")
        ttk.Label(header_frame, text="NEURO-PRODUCTIVITY SYSTEM", foreground="#666666", font=("Segoe UI", 8)).pack(side="top")
        
        # Status Indicator
        self.status_frame = tk.Frame(main_frame, bg=self.colors["panel"], padx=20, pady=20, relief="flat")
        self.status_frame.pack(fill="x", pady=(0, 30))
        
        self.status_dot = tk.Label(self.status_frame, text="●", font=("Arial", 24), bg=self.colors["panel"], fg="#666666")
        self.status_dot.pack(side="left")
        
        self._open_settings()

    def _open_settings(self):
        subprocess.run([sys.executable, str(BACKEND_DIR / "onboarding.py")])

    def _toggle_engine(self):
        if self.is_running:
            self._stop_engine()
        else:
            self._start_engine()

    def _start_engine(self):
        if self.server_process:
            return
            
        try:
            # Start main.py
            self.server_process = subprocess.Popen(
                [sys.executable, str(MAIN_SCRIPT)],
                cwd=str(BACKEND_DIR.parent),
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            self.is_running = True
            self._update_ui_state(True)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start engine: {e}")

    def _stop_engine(self):
        if self.server_process:
            self.server_process.terminate()
            self.server_process = None
            
        self.is_running = False
        self._update_ui_state(False)

    def _update_ui_state(self, running):
        if running:
            self.status_dot.config(fg=self.colors["success"])
            self.status_text.config(text="SYSTEM ONLINE", fg="white")
            self.btn_toggle.config(text="TERMINATE SYSTEM", bg=self.colors["danger"])
            self.btn_dashboard.config(state="normal", bg=self.colors["panel"], fg="white")
        else:
            self.status_dot.config(fg="#666666")
            self.status_text.config(text="SYSTEM OFFLINE", fg="#666666")
            self.btn_toggle.config(text="INITIALIZE SYSTEM", bg=self.colors["accent"])
            self.btn_dashboard.config(state="disabled", bg="#111111", fg="#444444")

    def _minimize_to_tray(self):
        self.root.withdraw()
        
        if not self.tray_icon and pystray:
            image = Image.new('RGB', (64, 64), (33, 158, 188))
            if ICON_PATH.exists():
                try:
                    image = Image.open(ICON_PATH)
                except:
                    pass
            
            menu = (
                item('Open Launcher', self._restore_from_tray),
                item('Stop Engine', self._stop_engine),
                item('Exit', self._quit_app)
            )
            
            self.tray_icon = pystray.Icon("flow_engine", image, "Flow Engine", menu)
            threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def _restore_from_tray(self, icon=None, item=None):
        if self.tray_icon:
            self.tray_icon.stop()
            self.tray_icon = None
        self.root.deiconify()

    def _on_close(self):
        if pystray:
            self._minimize_to_tray()
        else:
            self._quit_app()

    def _quit_app(self, icon=None, item=None):
        self._stop_engine()
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.quit()
        sys.exit(0)

if __name__ == "__main__":
    root = tk.Tk()
    app = FlowLauncher(root)
    root.mainloop()

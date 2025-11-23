import os
import sys
import subprocess
import threading
import time
import webbrowser
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

# Paths
ROOT = Path(__file__).parent.resolve()
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend-react"
BACKEND_MAIN = BACKEND_DIR / "main.py"
ONBOARDING = BACKEND_DIR / "onboarding.py"
CONFIG_FILE = ROOT / "user_config.json"

# Defaults
API_URL = "http://127.0.0.1:8000/api/health"
VITE_URL = "http://localhost:3000/"
PREVIEW_URL = "http://127.0.0.1:4173"

class ProcessManager:
    def __init__(self):
        self.backend_proc = None
        self.frontend_proc = None

    def start_backend(self):
        if self.backend_proc is not None:
            return
        try:
            self.backend_proc = subprocess.Popen(
                [sys.executable, str(BACKEND_MAIN)],
                cwd=str(ROOT),
                creationflags=(subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            )
        except Exception as e:
            self.backend_proc = None
            raise e

    def stop_backend(self):
        if self.backend_proc is not None:
            try:
                self.backend_proc.terminate()
            except Exception:
                pass
            self.backend_proc = None

    def start_frontend(self):
        if self.frontend_proc is not None:
            return
        # Prefer dev server via npm if available; fallback to preview or static serve
        npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
        try:
            if (FRONTEND_DIR / "package.json").exists():
                self.frontend_proc = subprocess.Popen(
                    [npm_cmd, "run", "dev"],
                    cwd=str(FRONTEND_DIR),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    creationflags=(subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                )
                # Detach log reader thread
                threading.Thread(target=self._pipe_logs, args=(self.frontend_proc.stdout,), daemon=True).start()
            else:
                raise FileNotFoundError("package.json not found in frontend-react")
        except Exception:
            # Fallback: try vite preview if built, else simple static server of dist
            try:
                self.frontend_proc = subprocess.Popen(
                    [npm_cmd, "run", "preview"],
                    cwd=str(FRONTEND_DIR),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    creationflags=(subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                )
                threading.Thread(target=self._pipe_logs, args=(self.frontend_proc.stdout,), daemon=True).start()
            except Exception:
                # As a last resort, serve dist with Python if it exists
                dist = FRONTEND_DIR / "dist"
                if dist.exists():
                    self.frontend_proc = subprocess.Popen(
                        [sys.executable, "-m", "http.server", "4173"],
                        cwd=str(dist),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        creationflags=(subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                    )
                    threading.Thread(target=self._pipe_logs, args=(self.frontend_proc.stdout,), daemon=True).start()
                else:
                    raise RuntimeError("Unable to start frontend. Ensure Node is installed or run `npm run build`.")

    def stop_frontend(self):
        if self.frontend_proc is not None:
            try:
                self.frontend_proc.terminate()
            except Exception:
                pass
            self.frontend_proc = None

    def _pipe_logs(self, pipe):
        try:
            for line in iter(pipe.readline, ''):
                # Keep logs available in console if launched from terminal
                sys.stdout.write("[frontend] " + line)
        except Exception:
            pass

class LauncherUI:
    def __init__(self, root):
        self.root = root
        self.root.title("FLOW ENGINE // LAUNCHER")
        self.root.geometry("500x350")
        self.root.resizable(False, False)

        self.pm = ProcessManager()

        self._setup_styles()
        self._build_ui()

        # Start backend automatically; start frontend after a short delay
        self.safe_start_backend()
        self.root.after(800, self.safe_start_frontend)
        # Open dashboard automatically on first ready check
        threading.Thread(target=self._wait_and_open_dashboard, daemon=True).start()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _setup_styles(self):
        self.style = ttk.Style()
        try:
            self.style.theme_use('clam')
        except Exception:
            pass
        
        # Futuristic Neon Palette
        self.colors = {
            "bg": "#050505",       # Deep Black
            "panel": "#101010",    # Dark Grey
            "fg": "#e0e0e0",       # Light Grey
            "header": "#00f3ff",   # Cyan Neon
            "accent": "#d900ff",   # Magenta Neon
            "ok": "#00ff9d",       # Neon Green
            "warn": "#ffea00",     # Neon Yellow
            "danger": "#ff0055",   # Neon Red
            "muted": "#666666",    # Muted Grey
            "button_bg": "#1a1a1a",
            "button_active": "#2a2a2a"
        }
        
        self.root.configure(bg=self.colors["bg"])
        
        # Configure Styles
        self.style.configure("TFrame", background=self.colors["bg"])
        self.style.configure("TLabel", background=self.colors["bg"], foreground=self.colors["fg"], font=("Segoe UI", 10))
        self.style.configure("Header.TLabel", background=self.colors["bg"], foreground=self.colors["header"], font=("Segoe UI", 24, "bold"))
        self.style.configure("Status.TLabel", background=self.colors["bg"], foreground=self.colors["fg"], font=("Consolas", 10))
        
        # Custom Button Style
        self.style.configure("TButton", 
                             background=self.colors["button_bg"], 
                             foreground=self.colors["header"], 
                             borderwidth=0, 
                             focuscolor=self.colors["accent"],
                             font=("Segoe UI", 10, "bold"),
                             padding=10)
        self.style.map("TButton",
                       background=[('active', self.colors["button_active"])],
                       foreground=[('active', self.colors["accent"])])

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=20)
        main.pack(fill="both", expand=True)

        # Header
        header_frame = ttk.Frame(main)
        header_frame.pack(fill="x", pady=(0, 20))
        
        # Decorative line
        canvas_line = tk.Canvas(header_frame, height=2, bg=self.colors["accent"], highlightthickness=0)
        canvas_line.pack(fill="x", side="bottom", pady=(5, 0))
        
        ttk.Label(header_frame, text="FLOW ENGINE", style="Header.TLabel").pack(side="left")
        ttk.Label(header_frame, text="v1.0", foreground=self.colors["accent"], background=self.colors["bg"], font=("Consolas", 10)).pack(side="right", anchor="s", pady=(0, 5))

        # Status Section
        status_frame = ttk.Frame(main)
        status_frame.pack(fill="x", pady=(0, 20))
        
        self.lbl_backend = ttk.Label(status_frame, text="[ ] Backend System", style="Status.TLabel")
        self.lbl_backend.pack(anchor="w", pady=2)
        
        self.lbl_frontend = ttk.Label(status_frame, text="[ ] Frontend Interface", style="Status.TLabel")
        self.lbl_frontend.pack(anchor="w", pady=2)

        # Controls Grid
        controls = ttk.Frame(main)
        controls.pack(fill="both", expand=True)
        controls.columnconfigure(0, weight=1)
        controls.columnconfigure(1, weight=1)
        
        self.btn_dashboard = ttk.Button(controls, text="LAUNCH DASHBOARD", command=self.open_dashboard)
        self.btn_dashboard.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        self.btn_settings = ttk.Button(controls, text="SETTINGS", command=self.open_settings)
        self.btn_settings.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        
        self.btn_restart = ttk.Button(controls, text="RESTART CORE", command=self.restart_backend)
        self.btn_restart.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        # Footer
        footer = ttk.Frame(main)
        footer.pack(fill="x", pady=(10, 0))
        self.btn_quit = ttk.Button(footer, text="TERMINATE", command=self.on_close)
        self.btn_quit.pack(fill="x")

        # Background checkers
        self._schedule_health_checks()

    def safe_start_backend(self):
        try:
            self.pm.start_backend()
            self._update_status(self.lbl_backend, "RUNNING", self.colors["ok"])
        except Exception as e:
            self._update_status(self.lbl_backend, "FAILED", self.colors["danger"])
            messagebox.showerror("Backend Error", f"Failed to start backend: {e}")

    def safe_start_frontend(self):
        try:
            self.pm.start_frontend()
            self._update_status(self.lbl_frontend, "STARTING", self.colors["warn"])
        except Exception as e:
            self._update_status(self.lbl_frontend, "FAILED", self.colors["danger"])
            messagebox.showwarning("Frontend Warning", str(e))

    def _update_status(self, label, status_text, color):
        label.config(text=f"[{status_text}] {label.cget('text').split(' ', 1)[1]}", foreground=color)

    def restart_backend(self):
        self.pm.stop_backend()
        self._update_status(self.lbl_backend, "STOPPED", self.colors["muted"])
        self.root.update()
        time.sleep(0.5)
        self.safe_start_backend()

    def open_settings(self):
        if not ONBOARDING.exists():
            messagebox.showwarning("Settings", "Onboarding/settings module not found.")
            return
        try:
            subprocess.Popen([sys.executable, str(ONBOARDING)], cwd=str(BACKEND_DIR))
        except Exception as e:
            messagebox.showerror("Settings Error", f"Failed to open settings: {e}")

    def open_dashboard(self):
        # Prefer detected running ports: vite dev (5173) first, then common vite ports (3000-3010), then preview/static (4173).
        if self._is_port_ready(5173):
            webbrowser.open("http://127.0.0.1:5173")
            return
        for p in range(3000, 3011):
            if self._is_port_ready(p):
                webbrowser.open(f"http://127.0.0.1:{p}")
                return
        if self._is_port_ready(4173):
            webbrowser.open(PREVIEW_URL)
            return
        # Otherwise, try custom VITE_URL only if its port responds.
        try:
            from urllib.parse import urlparse
            parsed = urlparse(VITE_URL)
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
            host = parsed.hostname or "127.0.0.1"
            if self._is_host_port_ready(host, port):
                webbrowser.open(VITE_URL)
                return
        except Exception:
            pass
        # Fallback: open backend docs if frontend isn't ready
        webbrowser.open("http://localhost:3000/")

    def _wait_and_open_dashboard(self):
        # Wait a bit for frontend to boot, then open once
        for _ in range(60):
            if self._is_port_ready(5173) or self._is_port_ready(4173):
                time.sleep(0.3)
                self.open_dashboard()
                return
            time.sleep(0.5)

    def _is_port_ready(self, port):
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.3)
            try:
                s.connect(("127.0.0.1", port))
                return True
            except Exception:
                return False

    def _is_host_port_ready(self, host, port):
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.3)
            try:
                s.connect((host, port))
                return True
            except Exception:
                return False

    def _schedule_health_checks(self):
        def tick():
            # Backend
            backend_ok = self._is_port_ready(8000)
            if backend_ok:
                self._update_status(self.lbl_backend, "ONLINE", self.colors["ok"])
            else:
                self._update_status(self.lbl_backend, "OFFLINE", self.colors["danger"])
            
            # Frontend
            vite_ok = self._is_port_ready(5173) or any(self._is_port_ready(p) for p in range(3000, 3011))
            fe_ok = vite_ok or self._is_port_ready(4173)
            
            if fe_ok:
                self._update_status(self.lbl_frontend, "ONLINE", self.colors["ok"])
            else:
                self._update_status(self.lbl_frontend, "LOADING", self.colors["warn"])
                
            self.root.after(1000, tick)
        self.root.after(1000, tick)

    def on_close(self):
        try:
            self.pm.stop_frontend()
            self.pm.stop_backend()
        finally:
            self.root.destroy()


def main():
    root = tk.Tk()
    app = LauncherUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()

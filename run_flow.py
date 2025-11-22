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
        self.root.title("Flow Engine Launcher")
        self.root.geometry("460x300")
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
        self.colors = {
            "bg": "#0b0b0d",
            "panel": "#151518",
            "fg": "#eaeaea",
            "muted": "#8a8a8a",
            "accent": "#219ebc",
            "ok": "#2a9d8f",
            "warn": "#ffb703",
            "danger": "#d00000",
        }
        self.root.configure(bg=self.colors["bg"])\

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=16)
        main.pack(fill="both", expand=True)

        header = ttk.Frame(main)
        header.pack(fill="x", pady=(0, 10))
        ttk.Label(header, text="FLOW ENGINE", font=("Segoe UI", 16, "bold")).pack(side="left")

        # Status
        status = ttk.Frame(main)
        status.pack(fill="x", pady=(0, 16))
        self.lbl_backend = ttk.Label(status, text="Backend: starting...")
        self.lbl_backend.pack(anchor="w")
        self.lbl_frontend = ttk.Label(status, text="Frontend: starting...")
        self.lbl_frontend.pack(anchor="w")

        # Controls
        controls = ttk.Frame(main)
        controls.pack(fill="x", pady=(8, 16))

        self.btn_settings = ttk.Button(controls, text="Open Settings", command=self.open_settings)
        self.btn_settings.grid(row=0, column=0, padx=6, pady=6)

        self.btn_dashboard = ttk.Button(controls, text="Open Dashboard", command=self.open_dashboard)
        self.btn_dashboard.grid(row=0, column=1, padx=6, pady=6)

        self.btn_restart = ttk.Button(controls, text="Restart Backend", command=self.restart_backend)
        self.btn_restart.grid(row=0, column=2, padx=6, pady=6)

        # Footer actions
        footer = ttk.Frame(main)
        footer.pack(fill="x")
        self.btn_quit = ttk.Button(footer, text="Quit", command=self.on_close)
        self.btn_quit.pack(side="right")

        # Background checkers
        self._schedule_health_checks()

    def safe_start_backend(self):
        try:
            self.pm.start_backend()
            self.lbl_backend.config(text="Backend: running")
        except Exception as e:
            self.lbl_backend.config(text=f"Backend: failed - {e}")
            messagebox.showerror("Backend Error", f"Failed to start backend: {e}")

    def safe_start_frontend(self):
        try:
            self.pm.start_frontend()
            self.lbl_frontend.config(text="Frontend: starting (dev server)")
        except Exception as e:
            self.lbl_frontend.config(text=f"Frontend: failed - {e}")
            messagebox.showwarning("Frontend Warning", str(e))

    def restart_backend(self):
        self.pm.stop_backend()
        time.sleep(0.2)
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
            self.lbl_backend.config(text=f"Backend: {'running' if backend_ok else 'starting...'}")
            # Frontend
            vite_ok = self._is_port_ready(5173) or any(self._is_port_ready(p) for p in range(3000, 3011))
            fe_ok = vite_ok or self._is_port_ready(4173)
            self.lbl_frontend.config(text=f"Frontend: {'running' if fe_ok else 'starting...'}")
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

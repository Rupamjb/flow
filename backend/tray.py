"""
Flow State Facilitator - System Tray
Runs the main application in the background and provides a system tray icon.
"""

import os
import sys
import threading
import subprocess
import time
from pathlib import Path
from PIL import Image, ImageDraw

try:
    import pystray
    from pystray import MenuItem as item
except ImportError:
    print("❌ pystray not installed. Install with: pip install pystray")
    sys.exit(1)

# Paths
BACKEND_DIR = Path(__file__).parent
MAIN_SCRIPT = BACKEND_DIR / "main.py"
ONBOARDING_SCRIPT = BACKEND_DIR / "onboarding.py"
ICON_PATH = BACKEND_DIR.parent / "extension" / "icon48.png"

class FlowTray:
    def __init__(self):
        self.icon = None
        self.server_process = None
        self.running = True
        
    def create_image(self):
        """Create a simple icon if file doesn't exist"""
        if ICON_PATH.exists():
            return Image.open(ICON_PATH)
        
        # Generate a placeholder icon (Blue Circle)
        width = 64
        height = 64
        image = Image.new('RGB', (width, height), (33, 158, 188))
        dc = ImageDraw.Draw(image)
        dc.ellipse((16, 16, 48, 48), fill='white')
        return image

    def start_server(self):
        """Start the FastAPI server"""
        # Run onboarding first if needed
        subprocess.run([sys.executable, str(ONBOARDING_SCRIPT)])
        
        print("🚀 Starting Flow Engine Server...")
        self.server_process = subprocess.Popen(
            [sys.executable, str(MAIN_SCRIPT)],
            cwd=str(BACKEND_DIR.parent),
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )

    def stop_server(self):
        """Stop the FastAPI server"""
        if self.server_process:
            print("🛑 Stopping server...")
            self.server_process.terminate()
            self.server_process = None

    def on_open_dashboard(self):
        """Open the dashboard in browser"""
        import webbrowser
        webbrowser.open("http://localhost:5173")  # Or localhost:8000 if serving static

    def on_exit(self, icon, item):
        """Exit the application"""
        self.stop_server()
        icon.stop()
        self.running = False
        sys.exit(0)

    def run(self):
        """Run the tray application"""
        image = self.create_image()
        
        menu = (
            item('Open Dashboard', self.on_open_dashboard),
            item('Exit', self.on_exit)
        )
        
        self.icon = pystray.Icon("flow_engine", image, "Flow Engine", menu)
        
        # Start server in background
        server_thread = threading.Thread(target=self.start_server, daemon=True)
        server_thread.start()
        
        # Run tray icon (blocking)
        self.icon.run()

if __name__ == "__main__":
    tray = FlowTray()
    tray.run()

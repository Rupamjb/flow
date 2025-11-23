import os
import sys
import threading
import time
import webview
import uvicorn
from main import app

# Global flag to control server loop
server_running = True

def start_server():
    """Start the FastAPI server in a separate thread"""
    # Use a specific port for the desktop app
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")

def on_closed():
    """Callback when window is closed"""
    print("Application closing...")
    # In a real production app, you might want a cleaner shutdown mechanism
    # For now, we rely on the main thread exiting
    os._exit(0)

if __name__ == '__main__':
    # Start server in a thread
    t = threading.Thread(target=start_server)
    t.daemon = True
    t.start()
    
    # Wait a moment for server to start
    time.sleep(1)
    
    # Create window
    webview.create_window(
        'Flow State Facilitator', 
        'http://127.0.0.1:8000',
        width=1200,
        height=800,
        resizable=True,
        min_size=(800, 600)
    )
    
    # Start webview
    webview.start(on_closed)

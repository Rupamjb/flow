"""
Flow State Facilitator - Blocker Overlay
A full-screen, semi-transparent overlay that blocks access to distracting windows.
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
import sys
import logging
from typing import Callable, Optional, Dict
from datetime import datetime, timedelta

class FlowBlocker:
    def __init__(self, on_resume: Optional[Callable] = None, on_break: Optional[Callable] = None):
        self.root = None
        self.active = False
        self.on_resume = on_resume
        self.on_break = on_break
        self.countdown_value = 3  # Short countdown before buttons enable
        self.resume_button = None
        self.break_button = None
        self.timer_label = None
        self.overlay_thread = None
        self.current_app_name = None  # Track which app triggered intervention

    def _create_overlay(self, message: str):
        """Create the Tkinter overlay window"""
        self.root = tk.Tk()
        self.root.title("Flow State Breach")
        
        # Fullscreen and topmost
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 0.95)  # 95% opacity
        self.root.configure(bg='#0a0a0a')  # Deep Void Black
        
        # Disable closing
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)
        
        # Center container
        container = tk.Frame(self.root, bg='#0a0a0a')
        container.place(relx=0.5, rely=0.5, anchor='center')
        
        # Header
        header = tk.Label(
            container, 
            text="FLOW STATE BREACH DETECTED", 
            font=("Segoe UI", 32, "bold"),
            fg="#d00000",  # Alarming Red
            bg='#0a0a0a'
        )
        header.pack(pady=(0, 20))
        
        # Subtext
        subtext = tk.Label(
            container,
            text=message,
            font=("Segoe UI", 16),
            fg="#ffffff",
            bg='#0a0a0a'
        )
        subtext.pack(pady=(0, 40))
        
        # Countdown Timer
        self.timer_label = tk.Label(
            container,
            text=str(self.countdown_value),
            font=("Consolas", 72, "bold"),
            fg="#ffb703",  # Neon Amber
            bg='#0a0a0a'
        )
        self.timer_label.pack(pady=20)
        
        # Buttons Container
        btn_container = tk.Frame(container, bg='#0a0a0a')
        btn_container.pack(pady=40)
        
        # Resume Button (Initially Disabled)
        # Wait Button (Good Choice)
        self.resume_button = tk.Button(
            btn_container,
            text="WAIT FOR BREAK (+STAMINA)",
            font=("Segoe UI", 14, "bold"),
            bg="#333333",
            fg="#888888",
            state="disabled",
            command=self._handle_resume,
            width=25,
            height=2,
            relief="flat"
        )
        self.resume_button.pack(side="left", padx=20)
        
        # Open Anyway Button (Bad Choice)
        self.break_button = tk.Button(
            btn_container,
            text="OPEN ANYWAY (-RESILIENCE)",
            font=("Segoe UI", 14, "bold"),
            bg="#333333",
            fg="#888888",
            state="disabled",
            command=self._handle_break,
            width=30,
            height=2,
            relief="flat"
        )
        self.break_button.pack(side="left", padx=20)
        
        # Start countdown
        self._update_countdown()
        
        self.root.mainloop()

    def _update_countdown(self):
        """Update the countdown timer"""
        if self.countdown_value > 0:
            self.countdown_value -= 1
            if self.timer_label:
                self.timer_label.config(text=str(self.countdown_value))
            self.root.after(1000, self._update_countdown)
        else:
            self._enable_buttons()

    def _enable_buttons(self):
        """Enable buttons after countdown"""
        if self.resume_button:
            self.resume_button.config(
                state="normal", 
                bg="#219ebc",  # Electric Blue
                fg="#ffffff",
                cursor="hand2"
            )
        
        if self.break_button:
            self.break_button.config(
                state="normal",
                bg="#d00000",  # Alarming Red
                fg="#ffffff",
                cursor="hand2"
            )
            
        if self.timer_label:
            self.timer_label.config(text="CHOOSE WISELY", font=("Segoe UI", 24))

    def _handle_resume(self):
        """Handle resume action - Close app/tab and grant rewards"""
        try:
            # Close the app/tab that triggered intervention
            if self.current_app_name:
                self.close_app_or_tab(self.current_app_name)
            
            if self.on_resume:
                self.on_resume()
                logging.getLogger("FlowEngine").info("Wait for break chosen (resume) - App closed")
        except Exception as e:
            logging.getLogger("FlowEngine").error(f"on_resume error: {e}")
        self.hide()

    def _handle_break(self):
        """Handle break action"""
        try:
            if self.on_break:
                self.on_break()
                logging.getLogger("FlowEngine").info("Open anyway chosen (break)")
        except Exception as e:
            logging.getLogger("FlowEngine").error(f"on_break error: {e}")
        self.hide()

    def show(self, message: str = "You are building Level 5 Resilience. Don't quit now.", app_name: Optional[str] = None):
        """Show the blocking overlay"""
        if self.active:
            return
            
        self.active = True
        self.countdown_value = 3
        self.current_app_name = app_name
        
        # Run Tkinter in a separate thread to avoid blocking main loop
        self.overlay_thread = threading.Thread(
            target=self._create_overlay,
            args=(message,),
            daemon=True
        )
        self.overlay_thread.start()

    def hide(self):
        """Hide the overlay"""
        if self.root:
            self.root.quit()
            self.root = None
        self.active = False
    
    def close_app_or_tab(self, app_name: str):
        """
        Close the app or tab that triggered the intervention.
        For browser tabs, this will be handled by the extension.
        For apps, we'll minimize/close the window.
        """
        try:
            import win32gui
            import win32con
            
            # Find window by process name
            def enum_windows_callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd):
                    window_text = win32gui.GetWindowText(hwnd)
                    if app_name.lower() in window_text.lower():
                        windows.append(hwnd)
                return True
            
            windows = []
            win32gui.EnumWindows(enum_windows_callback, windows)
            
            # Close or minimize the window
            for hwnd in windows:
                try:
                    win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                    logging.getLogger("FlowEngine").info(f"Attempted to close window: {app_name}")
                except Exception as e:
                    logging.getLogger("FlowEngine").warning(f"Could not close window: {e}")
        except ImportError:
            logging.getLogger("FlowEngine").warning("win32gui not available. Cannot close apps.")
        except Exception as e:
            logging.getLogger("FlowEngine").error(f"Error closing app: {e}")

# Standalone test
if __name__ == "__main__":
    print("Testing Flow Blocker...")
    
    def on_resume():
        print("✅ RESUMED WORK")
        
    def on_break():
        print("❌ TOOK A BREAK")
    
    blocker = FlowBlocker(on_resume=on_resume, on_break=on_break)
    blocker.show()
    
    # Keep main thread alive
    try:
        while blocker.active:
            time.sleep(0.1)
    except KeyboardInterrupt:
        blocker.hide()

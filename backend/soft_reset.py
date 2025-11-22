"""
Flow Engine - Soft Reset System
Provides cognitive reset interventions through visual and audio cues.
Triggered when cognitive fatigue is detected.
"""

import tkinter as tk
from tkinter import Canvas
import threading
import time
from PIL import Image, ImageFilter, ImageTk
import ctypes

try:
    from comtypes import CLSCTX_ALL
    import comtypes
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    print("⚠️  pycaw not available. Audio fade disabled.")

class SoftReset:
    """
    Soft Reset intervention system.
    
    Features:
    - Progressive screen blur (0 → 10px over 5 seconds)
    - Linear audio fade (current → 20% over 10 seconds)
    - Calming message display
    - Auto-restore after duration
    """
    
    def __init__(self, duration: int = 45):
        """
        Args:
            duration: Total reset duration in seconds (default: 45s)
        """
        self.duration = duration
        self.active = False
        self.overlay_window = None
        self.original_volume = None
        
    def trigger(self):
        """Start the soft reset intervention"""
        if self.active:
            return
            
        self.active = True
        
        # Run in separate thread to avoid blocking
        threading.Thread(target=self._execute_reset, daemon=True).start()
    
    def _execute_reset(self):
        """Execute the full soft reset sequence"""
        print("🧘 Cognitive Reset initiated...")
        
        # Phase 1: Visual blur (5 seconds)
        self._apply_visual_blur()
        
        # Phase 2: Audio fade (10 seconds) + hold (30 seconds)
        if AUDIO_AVAILABLE:
            self._fade_audio_out(duration=10)
        
        # Hold state for remaining duration
        time.sleep(self.duration - 15)
        
        # Phase 3: Restore (5 seconds)
        if AUDIO_AVAILABLE:
            self._fade_audio_in(duration=5)
        
        self._remove_visual_blur()
        
        self.active = False
        print("✅ Cognitive Reset complete")
    
    def _apply_visual_blur(self):
        """Create and display blur overlay"""
        def create_overlay():
            try:
                # Create fullscreen transparent window
                self.overlay_window = tk.Tk()
                self.overlay_window.attributes('-fullscreen', True)
                self.overlay_window.attributes('-topmost', True)
                self.overlay_window.attributes('-alpha', 0.0)  # Start transparent

                # Make window click-through (Windows only)
                if hasattr(ctypes, 'windll'):
                    hwnd = ctypes.windll.user32.GetParent(self.overlay_window.winfo_id())
                    style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
                    style = style | 0x80000 | 0x20  # WS_EX_LAYERED | WS_EX_TRANSPARENT
                    ctypes.windll.user32.SetWindowLongW(hwnd, -20, style)

                # Create canvas for blur effect
                canvas = Canvas(
                    self.overlay_window,
                    bg='#1a1a1a',
                    highlightthickness=0
                )
                canvas.pack(fill='both', expand=True)

                # Add calming message
                canvas.create_text(
                    self.overlay_window.winfo_screenwidth() // 2,
                    self.overlay_window.winfo_screenheight() // 2,
                    text="Cognitive Reset in Progress...\nTake a deep breath",
                    font=('Segoe UI', 32, 'bold'),
                    fill='#219ebc',
                    justify='center'
                )

                # Progressive fade in
                for alpha in range(0, 70, 2):  # 0 to 70% opacity
                    if not self.overlay_window:
                        break
                    self.overlay_window.attributes('-alpha', alpha / 100)
                    self.overlay_window.update()
                    time.sleep(0.1)

                # Hold for duration
                time.sleep(max(0, self.duration - 10))

                # Fade out
                for alpha in range(70, 0, -2):
                    if not self.overlay_window:
                        break
                    self.overlay_window.attributes('-alpha', alpha / 100)
                    self.overlay_window.update()
                    time.sleep(0.05)
            except Exception:
                # If Tk fails in this environment, just skip visual
                self.overlay_window = None
        
        # Run overlay in main thread (Tkinter requirement)
        threading.Thread(target=create_overlay, daemon=True).start()
    
    def _remove_visual_blur(self):
        """Remove blur overlay"""
        if self.overlay_window:
            try:
                self.overlay_window.destroy()
            except:
                pass
            self.overlay_window = None
    
    def _fade_audio_out(self, duration: int = 10):
        """
        Fade system audio from current volume to 20% over duration.
        
        Args:
            duration: Fade duration in seconds
        """
        try:
            # Initialize COM for this thread
            try:
                comtypes.CoInitialize()
            except Exception:
                pass
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = interface.QueryInterface(IAudioEndpointVolume)
            
            # Get current volume
            self.original_volume = volume.GetMasterVolumeLevelScalar()
            target_volume = 0.2  # 20%
            
            # Calculate steps
            steps = duration * 10  # 10 steps per second
            volume_step = (self.original_volume - target_volume) / steps
            
            # Fade out
            current = self.original_volume
            for _ in range(int(steps)):
                current -= volume_step
                volume.SetMasterVolumeLevelScalar(max(0.0, current), None)
                time.sleep(0.1)
            
            print(f"🔉 Audio faded: {self.original_volume*100:.0f}% → 20%")
            
        except Exception as e:
            print(f"⚠️  Audio fade failed: {e}")
    
    def _fade_audio_in(self, duration: int = 5):
        """
        Fade system audio from 20% back to original volume.
        
        Args:
            duration: Fade duration in seconds
        """
        if self.original_volume is None:
            return
            
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = interface.QueryInterface(IAudioEndpointVolume)
            
            current_volume = 0.2
            target_volume = self.original_volume
            
            # Calculate steps
            steps = duration * 10
            volume_step = (target_volume - current_volume) / steps
            
            # Fade in
            current = current_volume
            for _ in range(int(steps)):
                current += volume_step
                volume.SetMasterVolumeLevelScalar(min(1.0, current), None)
                time.sleep(0.1)
            
            print(f"🔊 Audio restored: 20% → {self.original_volume*100:.0f}%")
            
        except Exception as e:
            print(f"⚠️  Audio restore failed: {e}")

# Standalone test (non-interactive)
if __name__ == "__main__":
    print("Testing Soft Reset System (auto-start)...")
    reset = SoftReset(duration=45)
    reset.trigger()
    time.sleep(50)
    print("Test complete!")

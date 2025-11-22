"""
Flow State Facilitator - Micro-Interventions
Gentle cognitive fatigue interventions: screen blur and audio fade.
"""

import time
import threading
from typing import Optional

# Audio control (Windows-specific)
try:
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    from comtypes import CLSCTX_ALL
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    print("⚠️  pycaw not available. Audio fade disabled.")

# For screen effects, we'll use a simple approach
try:
    from PIL import Image, ImageFilter
    import win32gui
    import win32ui
    import win32con
    SCREEN_EFFECTS_AVAILABLE = True
except ImportError:
    SCREEN_EFFECTS_AVAILABLE = False
    print("⚠️  PIL/pywin32 not available. Screen blur disabled.")


class InterventionManager:
    """Manage micro-interventions for cognitive fatigue"""
    
    def __init__(self):
        self.audio_controller = AudioController() if AUDIO_AVAILABLE else None
        self.screen_controller = ScreenEffectController() if SCREEN_EFFECTS_AVAILABLE else None
    
    def trigger_soft_reset(self, duration: int = 10):
        """
        Trigger a soft reset intervention:
        - Apply screen blur
        - Fade out audio
        """
        print("🧘 Triggering Soft Reset intervention...")
        
        # Start both interventions in parallel
        threads = []
        
        if self.screen_controller:
            blur_thread = threading.Thread(
                target=self.screen_controller.apply_blur_overlay,
                args=(duration,),
                daemon=True
            )
            threads.append(blur_thread)
            blur_thread.start()
        
        if self.audio_controller:
            audio_thread = threading.Thread(
                target=self.audio_controller.fade_out,
                args=(duration,),
                daemon=True
            )
            threads.append(audio_thread)
            audio_thread.start()
        
        # Wait for interventions to complete
        for thread in threads:
            thread.join()
        
        print("✅ Soft Reset complete")


class AudioController:
    """Control system audio volume"""
    
    def __init__(self):
        if not AUDIO_AVAILABLE:
            raise RuntimeError("pycaw is required for audio control")
        
        self.original_volume = None
        self._initialize_audio()
    
    def _initialize_audio(self):
        """Initialize audio endpoint"""
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            self.volume = interface.QueryInterface(IAudioEndpointVolume)
            self.original_volume = self.volume.GetMasterVolumeLevelScalar()
        except Exception as e:
            print(f"❌ Failed to initialize audio: {e}")
            self.volume = None
    
    def fade_out(self, duration: int = 10):
        """Linear cross-fade volume reduction"""
        if not self.volume:
            print("⚠️  Audio control not available")
            return
        
        print(f"🔊 Fading out audio over {duration} seconds...")
        
        try:
            start_volume = self.volume.GetMasterVolumeLevelScalar()
            steps = 20  # Number of fade steps
            step_duration = duration / steps
            
            for i in range(steps + 1):
                # Linear fade from start_volume to 0
                new_volume = start_volume * (1 - i / steps)
                self.volume.SetMasterVolumeLevelScalar(new_volume, None)
                time.sleep(step_duration)
            
            print("🔇 Audio faded to 0%")
            
        except Exception as e:
            print(f"❌ Audio fade error: {e}")
    
    def fade_in(self, duration: int = 5):
        """Fade audio back in"""
        if not self.volume or self.original_volume is None:
            return
        
        print(f"🔊 Fading in audio over {duration} seconds...")
        
        try:
            steps = 20
            step_duration = duration / steps
            
            for i in range(steps + 1):
                new_volume = self.original_volume * (i / steps)
                self.volume.SetMasterVolumeLevelScalar(new_volume, None)
                time.sleep(step_duration)
            
            print("🔊 Audio restored")
            
        except Exception as e:
            print(f"❌ Audio fade in error: {e}")
    
    def restore_volume(self):
        """Restore original volume immediately"""
        if self.volume and self.original_volume is not None:
            self.volume.SetMasterVolumeLevelScalar(self.original_volume, None)


class ScreenEffectController:
    """Apply visual effects to the screen"""
    
    def __init__(self):
        if not SCREEN_EFFECTS_AVAILABLE:
            raise RuntimeError("PIL and pywin32 required for screen effects")
    
    def apply_blur_overlay(self, duration: int = 10):
        """
        Apply a blur effect overlay to the screen.
        For hackathon: simplified version that just logs.
        Production: would create a transparent topmost window with blurred background.
        """
        print(f"🌫️  Applying screen blur for {duration} seconds...")
        
        # Simplified for hackathon - just simulate the effect
        # In production, this would:
        # 1. Capture screenshot
        # 2. Apply Gaussian blur
        # 3. Display in transparent topmost window
        # 4. Gradually increase blur intensity
        
        time.sleep(duration)
        print("✅ Screen blur removed")
    
    def capture_screen(self):
        """Capture current screen (for blur effect)"""
        # This would use win32gui to capture the screen
        # Then PIL to apply blur filter
        pass


# Standalone test
if __name__ == "__main__":
    print("Testing Intervention Manager...")
    
    manager = InterventionManager()
    
    print("\n1. Testing audio fade...")
    if manager.audio_controller:
        manager.audio_controller.fade_out(duration=5)
        time.sleep(1)
        manager.audio_controller.fade_in(duration=3)
    
    print("\n2. Testing soft reset...")
    manager.trigger_soft_reset(duration=5)
    
    print("\n✅ Tests complete")

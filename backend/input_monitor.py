"""
Flow Engine - Input Monitor (APM Tracking)
Tracks keyboard and mouse activity to calculate Actions Per Minute.
Layer 3 of the tri-layer flow detection system.
"""

import time
import threading
from collections import deque
from typing import Callable, Optional
from datetime import datetime, timedelta

try:
    from pynput import keyboard, mouse
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False
    print("⚠️  pynput not available. APM tracking disabled.")

class InputMonitor:
    """Monitor keyboard and mouse input to calculate APM"""
    
    def __init__(self, callback: Optional[Callable] = None):
        if not PYNPUT_AVAILABLE:
            raise RuntimeError("pynput is required for input monitoring")
        
        self.callback = callback
        self.monitoring = False
        
        # Event tracking
        self.events = deque(maxlen=1000)  # Last 1000 events
        self.keyboard_events = 0
        self.mouse_events = 0
        self.scroll_events = 0
        
        # Listeners
        self.keyboard_listener = None
        self.mouse_listener = None
        
        # APM calculation
        self.current_apm = 0.0
        self.last_apm_update = time.time()
        
    def on_keyboard_press(self, key):
        """Keyboard press event handler"""
        try:
            self.keyboard_events += 1
            self.events.append({
                'type': 'keyboard',
                'timestamp': time.time(),
                'key': str(key)
            })
            self._update_apm()
        except Exception as e:
            pass
    
    def on_mouse_click(self, x, y, button, pressed):
        """Mouse click event handler"""
        if pressed:  # Only count press, not release
            self.mouse_events += 1
            self.events.append({
                'type': 'mouse_click',
                'timestamp': time.time(),
                'button': str(button)
            })
            self._update_apm()
    
    def on_mouse_scroll(self, x, y, dx, dy):
        """Mouse scroll event handler"""
        self.scroll_events += 1
        self.events.append({
            'type': 'mouse_scroll',
            'timestamp': time.time(),
            'delta': dy
        })
        self._update_apm()
    
    def _update_apm(self):
        """Calculate current APM based on recent events"""
        now = time.time()
        
        # Only update every 2 seconds to avoid excessive calculations
        if now - self.last_apm_update < 2.0:
            return
        
        self.last_apm_update = now
        
        # Count events in last 60 seconds
        one_minute_ago = now - 60
        recent_events = [e for e in self.events if e['timestamp'] > one_minute_ago]
        
        self.current_apm = len(recent_events)
        
        # Call callback if provided
        if self.callback:
            self.callback({
                'apm': self.current_apm,
                'keyboard_events': sum(1 for e in recent_events if e['type'] == 'keyboard'),
                'mouse_events': sum(1 for e in recent_events if e['type'] == 'mouse_click'),
                'scroll_events': sum(1 for e in recent_events if e['type'] == 'mouse_scroll')
            })
    
    def get_apm(self) -> float:
        """Get current APM"""
        return self.current_apm
    
    def get_activity_pattern(self) -> str:
        """
        Determine activity pattern based on APM and event types
        Returns: 'active', 'passive', or 'idle'
        """
        now = time.time()
        one_minute_ago = now - 60
        recent_events = [e for e in self.events if e['timestamp'] > one_minute_ago]
        
        if not recent_events:
            return 'idle'
        
        keyboard_count = sum(1 for e in recent_events if e['type'] == 'keyboard')
        scroll_count = sum(1 for e in recent_events if e['type'] == 'mouse_scroll')
        
        # High keyboard activity = active work
        if keyboard_count > 30:
            return 'active'
        
        # Low keyboard but high scroll = passive reading
        if keyboard_count < 10 and scroll_count > 20:
            return 'passive'
        
        # Some activity but not much
        if self.current_apm > 10:
            return 'active'
        
        return 'idle'
    
    def is_idle(self, threshold_seconds: int = 300) -> bool:
        """Check if user has been idle for threshold seconds"""
        if not self.events:
            return True
        
        last_event_time = self.events[-1]['timestamp']
        return (time.time() - last_event_time) > threshold_seconds
    
    def start_monitoring(self):
        """Start monitoring keyboard and mouse input"""
        if self.monitoring:
            return
        
        self.monitoring = True
        
        # Start keyboard listener
        self.keyboard_listener = keyboard.Listener(
            on_press=self.on_keyboard_press
        )
        self.keyboard_listener.start()
        
        # Start mouse listener
        self.mouse_listener = mouse.Listener(
            on_click=self.on_mouse_click,
            on_scroll=self.on_mouse_scroll
        )
        self.mouse_listener.start()
        
        print("⌨️  Input monitoring started (APM tracking active)")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
        
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        
        if self.mouse_listener:
            self.mouse_listener.stop()
        
        print("🛑 Input monitoring stopped")
    
    def get_stats(self) -> dict:
        """Get current monitoring stats"""
        return {
            'apm': self.current_apm,
            'total_keyboard_events': self.keyboard_events,
            'total_mouse_events': self.mouse_events,
            'total_scroll_events': self.scroll_events,
            'activity_pattern': self.get_activity_pattern(),
            'is_idle': self.is_idle(),
            'recent_events_count': len(self.events)
        }

# Standalone test
if __name__ == "__main__":
    if not PYNPUT_AVAILABLE:
        print("❌ This module requires pynput. Install with: pip install pynput")
        exit(1)
    
    def on_apm_update(data):
        print(f"📊 APM: {data['apm']:.1f} | "
              f"Keyboard: {data['keyboard_events']} | "
              f"Mouse: {data['mouse_events']} | "
              f"Scroll: {data['scroll_events']}")
    
    monitor = InputMonitor(callback=on_apm_update)
    monitor.start_monitoring()
    
    print("Monitoring input. Press Ctrl+C to stop...")
    print("Try typing, clicking, and scrolling to see APM changes.")
    
    try:
        while True:
            time.sleep(5)
            stats = monitor.get_stats()
            print(f"\n📈 Current Stats:")
            print(f"   APM: {stats['apm']:.1f}")
            print(f"   Pattern: {stats['activity_pattern']}")
            print(f"   Idle: {stats['is_idle']}")
    except KeyboardInterrupt:
        monitor.stop_monitoring()
        print("\n👋 Monitoring stopped")

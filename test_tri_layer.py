"""
Test script to verify tri-layer flow detection and DND activation
"""
import sys
import time
sys.path.insert(0, 'backend')

from main import state, enable_dnd, _check_and_auto_start_flow
from datetime import datetime, timedelta
import asyncio

print("=" * 60)
print("Tri-Layer Flow Detection Test")
print("=" * 60)

# Test 1: Check initial state
print("\n1. Initial State:")
print(f"   Layer1 productive start: {state.layer1_productive_start}")
print(f"   Layer2 last distraction: {state.layer2_last_distraction}")
print(f"   Layer3 active streak: {state.active_streak_start}")
print(f"   Flow threshold: {state.flow_detection_threshold_seconds}s ({state.flow_detection_threshold_seconds/60} min)")
print(f"   Is running: {state.is_running}")

# Test 2: Simulate Layer 1 (productive app)
print("\n2. Simulating Layer 1 (Productive App):")
state.layer1_productive_start = datetime.now()
print(f"   Layer1 started at: {state.layer1_productive_start}")

# Test 3: Simulate Layer 2 (no distractions)
print("\n3. Simulating Layer 2 (No Distractions):")
state.layer2_last_distraction = None
print("   Layer2: No distractions (active)")

# Test 4: Simulate Layer 3 (active input)
print("\n4. Simulating Layer 3 (Active Input):")
state.active_streak_start = datetime.now()
print(f"   Layer3 started at: {state.active_streak_start}")

# Test 5: Check if all layers are active (but not long enough)
print("\n5. Checking tri-layer status (immediately):")
asyncio.run(_check_and_auto_start_flow())
print(f"   Is running: {state.is_running}")

# Test 6: Simulate time passing (set times to be old enough)
print("\n6. Simulating time passage (setting times to be old enough):")
state.layer1_productive_start = datetime.now() - timedelta(seconds=state.flow_detection_threshold_seconds + 10)
state.active_streak_start = datetime.now() - timedelta(seconds=state.flow_detection_threshold_seconds + 10)
print(f"   Layer1 started: {state.layer1_productive_start} (old enough)")
print(f"   Layer3 started: {state.active_streak_start} (old enough)")

# Reset running state for test
state.is_running = False

# Test 7: Check tri-layer again (should trigger)
print("\n7. Checking tri-layer status (after threshold):")
asyncio.run(_check_and_auto_start_flow())
print(f"   Is running: {state.is_running}")

# Test 8: Test DND activation
print("\n8. Testing DND Activation:")
result = enable_dnd()
if result:
    print("   [OK] DND enabled successfully")
    print(f"   Previous toast setting: {state.dnd_prev_value}")
    print(f"   Previous Focus Assist: {state.focus_assist_prev_value}")
else:
    print("   [ERROR] DND activation failed")

print("\n" + "=" * 60)
print("Test Complete")
print("=" * 60)


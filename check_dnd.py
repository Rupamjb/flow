"""Check current Windows DND settings"""
import winreg

print("=" * 60)
print("Current Windows DND Settings")
print("=" * 60)

# Check Focus Assist
qh_key = r"Software\Microsoft\Windows\CurrentVersion\QuietHours"
try:
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, qh_key, 0, winreg.KEY_READ) as key:
        val, _ = winreg.QueryValueEx(key, "FocusAssist")
        status = {0: "Off", 1: "Priority Only", 2: "Alarms Only"}.get(val, f"Unknown ({val})")
        print(f"\nFocus Assist: {status}")
        print(f"  Value: {val} (0=Off, 1=Priority, 2=Alarms only)")
        if val == 2:
            print("  [OK] DND is ACTIVE - Only alarms will show")
        else:
            print("  [INFO] DND is not fully active")
except Exception as e:
    print(f"\nFocus Assist: Error reading - {e}")

# Check Toast Notifications
notif_key = r"Software\Microsoft\Windows\CurrentVersion\Notifications\Settings"
try:
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, notif_key, 0, winreg.KEY_READ) as key:
        try:
            toast_val, _ = winreg.QueryValueEx(key, "NOC_GLOBAL_SETTING_TOASTS_ENABLED")
            status = "Disabled" if toast_val == 0 else "Enabled"
            print(f"\nToast Notifications: {status}")
            print(f"  Value: {toast_val} (0=Disabled, 1=Enabled)")
            if toast_val == 0:
                print("  [OK] Toast notifications are DISABLED")
            else:
                print("  [INFO] Toast notifications are enabled")
        except FileNotFoundError:
            print("\nToast Notifications: Setting not found in registry")
except Exception as e:
    print(f"\nToast Notifications: Error reading - {e}")

print("\n" + "=" * 60)
print("Summary:")
print("  - Focus Assist should be set to 2 (Alarms Only)")
print("  - Toast Notifications should be set to 0 (Disabled)")
print("  - Check Windows Action Center to see DND status")
print("=" * 60)


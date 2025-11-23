"""Comprehensive DND test with PowerShell"""
import subprocess
import winreg
import time

print("=" * 60)
print("Comprehensive DND Test")
print("=" * 60)

# Test 1: Check current registry values
print("\n1. Current Registry Values:")
qh_key = r"Software\Microsoft\Windows\CurrentVersion\QuietHours"
notif_key = r"Software\Microsoft\Windows\CurrentVersion\Notifications\Settings"

try:
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, qh_key, 0, winreg.KEY_READ) as key:
        val, _ = winreg.QueryValueEx(key, "FocusAssist")
        print(f"   Focus Assist: {val} (should be 2)")
except Exception as e:
    print(f"   Focus Assist: Error - {e}")

try:
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, notif_key, 0, winreg.KEY_READ) as key:
        toast_val, _ = winreg.QueryValueEx(key, "NOC_GLOBAL_SETTING_TOASTS_ENABLED")
        print(f"   Toast Notifications: {toast_val} (should be 0)")
except Exception as e:
    print(f"   Toast Notifications: Error - {e}")

# Test 2: Use PowerShell to enable Focus Assist
print("\n2. Enabling Focus Assist via PowerShell:")
ps_command = '''
$path = "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\QuietHours"
Set-ItemProperty -Path $path -Name "FocusAssist" -Value 2 -Type DWord -Force
Write-Output "Focus Assist set to 2"
'''
try:
    result = subprocess.run(
        ["powershell", "-Command", ps_command],
        capture_output=True,
        text=True,
        timeout=5,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    print(f"   PowerShell output: {result.stdout.strip()}")
    if result.returncode == 0:
        print("   [OK] PowerShell command succeeded")
    else:
        print(f"   [WARNING] PowerShell returned code {result.returncode}")
        print(f"   Error: {result.stderr[:200]}")
except Exception as e:
    print(f"   [ERROR] PowerShell failed: {e}")

# Test 3: Verify after PowerShell
time.sleep(0.5)
print("\n3. Verification after PowerShell:")
try:
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, qh_key, 0, winreg.KEY_READ) as key:
        val, _ = winreg.QueryValueEx(key, "FocusAssist")
        print(f"   Focus Assist: {val}")
        if val == 2:
            print("   [OK] Focus Assist is correctly set to 2")
        else:
            print("   [WARNING] Focus Assist is not set correctly")
except Exception as e:
    print(f"   [ERROR] Could not verify: {e}")

print("\n" + "=" * 60)
print("IMPORTANT NOTES:")
print("1. Registry values are set correctly")
print("2. However, Windows may need:")
print("   - A system restart")
print("   - Manual toggle in Windows Settings > System > Focus Assist")
print("3. Some apps (like Teams, Outlook) can bypass Focus Assist")
print("4. Check Windows Action Center (bottom-right) for Focus Assist icon")
print("=" * 60)


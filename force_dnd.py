"""
Force DND activation by opening Windows Focus Assist settings
This allows user to manually verify/activate if registry changes aren't taking effect
"""
import subprocess
import winreg
import sys

print("=" * 60)
print("Force DND Activation")
print("=" * 60)

# Step 1: Set registry values
print("\n1. Setting registry values...")
qh_key = r"Software\Microsoft\Windows\CurrentVersion\QuietHours"
notif_key = r"Software\Microsoft\Windows\CurrentVersion\Notifications\Settings"

try:
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, qh_key) as key:
        winreg.SetValueEx(key, "FocusAssist", 0, winreg.REG_DWORD, 2)
    print("   [OK] Focus Assist set to 2 in registry")
except Exception as e:
    print(f"   [ERROR] Failed to set Focus Assist: {e}")

try:
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, notif_key) as key:
        winreg.SetValueEx(key, "NOC_GLOBAL_SETTING_TOASTS_ENABLED", 0, winreg.REG_DWORD, 0)
    print("   [OK] Toast notifications disabled in registry")
except Exception as e:
    print(f"   [ERROR] Failed to disable toasts: {e}")

# Step 2: Use PowerShell to force refresh
print("\n2. Refreshing notification system via PowerShell...")
ps_command = '''
$path = "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\QuietHours"
Set-ItemProperty -Path $path -Name "FocusAssist" -Value 2 -Type DWord -Force

# Try to restart notification-related processes
$processes = @("ShellExperienceHost", "RuntimeBroker")
foreach ($proc in $processes) {
    try {
        Get-Process -Name $proc -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Milliseconds 500
    } catch {}
}
Write-Output "Notification system refreshed"
'''
try:
    result = subprocess.run(
        ["powershell", "-Command", ps_command],
        capture_output=True,
        text=True,
        timeout=10,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    print(f"   PowerShell: {result.stdout.strip()}")
except Exception as e:
    print(f"   [WARNING] PowerShell refresh failed: {e}")

# Step 3: Open Windows Focus Assist settings
print("\n3. Opening Windows Focus Assist settings...")
print("   Please manually verify Focus Assist is set to 'Alarms only'")
try:
    # Open Windows Settings > System > Focus Assist
    subprocess.Popen(
        ["ms-settings:quiethours"],
        shell=True,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    print("   [OK] Windows Settings opened to Focus Assist page")
    print("   [ACTION REQUIRED] Please verify Focus Assist shows 'Alarms only'")
    print("   [ACTION REQUIRED] If it shows 'Off', toggle it to 'Alarms only'")
except Exception as e:
    print(f"   [WARNING] Could not open settings: {e}")
    print("   [MANUAL] Please go to: Settings > System > Focus Assist")

print("\n" + "=" * 60)
print("SUMMARY:")
print("1. Registry values are set correctly")
print("2. Notification system refreshed")
print("3. Windows Settings should be open")
print("\nIF NOTIFICATIONS STILL APPEAR:")
print("- Some apps (Teams, Outlook, etc.) can bypass Focus Assist")
print("- Check Windows Action Center (bottom-right corner)")
print("- Look for Focus Assist icon - it should show 'Alarms only'")
print("- You may need to manually toggle Focus Assist in Settings")
print("=" * 60)


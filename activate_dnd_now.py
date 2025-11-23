"""
Comprehensive DND activation with Windows Settings opening
"""
import winreg
import subprocess
import sys
import time

print("=" * 70)
print("COMPREHENSIVE DND ACTIVATION")
print("=" * 70)

# Step 1: Set all registry values
print("\n[1/4] Setting Registry Values...")
qh_key = r"Software\Microsoft\Windows\CurrentVersion\QuietHours"
notif_key = r"Software\Microsoft\Windows\CurrentVersion\Notifications\Settings"

registry_changes = [
    (qh_key, "FocusAssist", 2),
    (notif_key, "NOC_GLOBAL_SETTING_TOASTS_ENABLED", 0),
    (notif_key, "NOC_GLOBAL_SETTING_BANNER_ENABLED", 0),
    (notif_key, "NOC_GLOBAL_SETTING_SOUND_ENABLED", 0),
]

for key_path, value_name, value in registry_changes:
    try:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            winreg.SetValueEx(key, value_name, 0, winreg.REG_DWORD, value)
        print(f"   [OK] {value_name} = {value}")
    except Exception as e:
        print(f"   [SKIP] {value_name}: {e}")

# Step 2: PowerShell comprehensive activation
print("\n[2/4] Running PowerShell Activation Script...")
ps_command = '''
# Set all registry values
$qhPath = "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\QuietHours"
$notifPath = "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Notifications\\Settings"

Set-ItemProperty -Path $qhPath -Name "FocusAssist" -Value 2 -Type DWord -Force
Set-ItemProperty -Path $notifPath -Name "NOC_GLOBAL_SETTING_TOASTS_ENABLED" -Value 0 -Type DWord -Force -ErrorAction SilentlyContinue
Set-ItemProperty -Path $notifPath -Name "NOC_GLOBAL_SETTING_BANNER_ENABLED" -Value 0 -Type DWord -Force -ErrorAction SilentlyContinue
Set-ItemProperty -Path $notifPath -Name "NOC_GLOBAL_SETTING_SOUND_ENABLED" -Value 0 -Type DWord -Force -ErrorAction SilentlyContinue

# Restart notification processes
$processes = @("ShellExperienceHost", "RuntimeBroker")
foreach ($proc in $processes) {
    try {
        Get-Process -Name $proc -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Milliseconds 300
    } catch {}
}

# Broadcast settings change
$code = @'
[DllImport("user32.dll", CharSet=CharSet.Auto)]
public static extern IntPtr SendMessageTimeout(
    IntPtr hWnd, uint Msg, IntPtr wParam, string lParam,
    uint fuFlags, uint uTimeout, out IntPtr lpdwResult);
'@
try {
    $type = Add-Type -MemberDefinition $code -Name User32 -Namespace Win32Functions -PassThru -ErrorAction SilentlyContinue
    if ($type) {
        $HWND_BROADCAST = [IntPtr]0xffff
        $WM_SETTINGCHANGE = 0x1a
        $result = [IntPtr]::Zero
        $type::SendMessageTimeout($HWND_BROADCAST, $WM_SETTINGCHANGE, [IntPtr]::Zero, "UserPreferences", 2, 5000, [ref]$result)
    }
} catch {}

Write-Output "Registry and services updated"
'''
try:
    result = subprocess.run(
        ["powershell", "-ExecutionPolicy", "Bypass", "-Command", ps_command],
        capture_output=True,
        text=True,
        timeout=15,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    print(f"   {result.stdout.strip()}")
    if result.stderr:
        print(f"   [WARNING] {result.stderr[:200]}")
except Exception as e:
    print(f"   [ERROR] {e}")

# Step 3: Open Windows Settings
print("\n[3/4] Opening Windows Focus Assist Settings...")
print("   [ACTION REQUIRED] A Windows Settings window should open")
print("   [ACTION REQUIRED] Please verify Focus Assist is set to 'Alarms only'")
print("   [ACTION REQUIRED] If it shows 'Off', click to toggle it to 'Alarms only'")
try:
    subprocess.Popen(
        ["ms-settings:quiethours"],
        shell=True,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    print("   [OK] Windows Settings opened")
except Exception as e:
    print(f"   [ERROR] Could not open settings: {e}")
    print("   [MANUAL] Please go to: Settings > System > Focus Assist")

# Step 4: Wait and verify
time.sleep(2)
print("\n[4/4] Final Verification...")
try:
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, qh_key, 0, winreg.KEY_READ) as key:
        val, _ = winreg.QueryValueEx(key, "FocusAssist")
        if val == 2:
            print(f"   [OK] Focus Assist registry: {val} (correct)")
        else:
            print(f"   [WARNING] Focus Assist registry: {val} (expected 2)")
except Exception as e:
    print(f"   [ERROR] Could not verify: {e}")

print("\n" + "=" * 70)
print("IMPORTANT: MANUAL ACTION REQUIRED")
print("=" * 70)
print("Windows Focus Assist often requires manual activation.")
print("\nDO THIS NOW:")
print("1. Look for the Windows Settings window that opened")
print("2. In Focus Assist settings, toggle it to 'Alarms only'")
print("3. Check the Action Center (bottom-right corner)")
print("4. You should see a Focus Assist icon when it's active")
print("\nWHY NOTIFICATIONS MAY STILL APPEAR:")
print("- Some apps (Teams, Outlook, Discord) bypass Focus Assist")
print("- These apps need to be disabled individually in:")
print("  Settings > System > Notifications")
print("=" * 70)


"""
Advanced DND activation using multiple methods
"""
import winreg
import subprocess
import ctypes
import sys

print("=" * 60)
print("Advanced DND Activation Test")
print("=" * 60)

# Method 1: Registry (already done)
print("\n1. Setting Registry Values...")
qh_key = r"Software\Microsoft\Windows\CurrentVersion\QuietHours"
notif_key = r"Software\Microsoft\Windows\CurrentVersion\Notifications\Settings"

try:
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, qh_key) as key:
        winreg.SetValueEx(key, "FocusAssist", 0, winreg.REG_DWORD, 2)
    print("   [OK] Focus Assist = 2")
except Exception as e:
    print(f"   [ERROR] {e}")

try:
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, notif_key) as key:
        winreg.SetValueEx(key, "NOC_GLOBAL_SETTING_TOASTS_ENABLED", 0, winreg.REG_DWORD, 0)
    print("   [OK] Toast Notifications = 0 (disabled)")
except Exception as e:
    print(f"   [ERROR] {e}")

# Method 2: Additional registry keys for comprehensive blocking
print("\n2. Setting Additional Notification Registry Keys...")
additional_keys = [
    (r"Software\Microsoft\Windows\CurrentVersion\Notifications\Settings\Windows.SystemToast.SecurityAndMaintenance", "Enabled", 0),
    (r"Software\Microsoft\Windows\CurrentVersion\Notifications\Settings", "NOC_GLOBAL_SETTING_BANNER_ENABLED", 0),
    (r"Software\Microsoft\Windows\CurrentVersion\Notifications\Settings", "NOC_GLOBAL_SETTING_SOUND_ENABLED", 0),
]

for key_path, value_name, value in additional_keys:
    try:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            winreg.SetValueEx(key, value_name, 0, winreg.REG_DWORD, value)
        print(f"   [OK] {key_path}\\{value_name} = {value}")
    except Exception as e:
        print(f"   [SKIP] {key_path}: {e}")

# Method 3: Use PowerShell with Windows Runtime API
print("\n3. Using PowerShell with Windows Runtime API...")
ps_command = '''
# Force enable Focus Assist
$path = "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\QuietHours"
Set-ItemProperty -Path $path -Name "FocusAssist" -Value 2 -Type DWord -Force

# Try to use Windows Runtime API
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | ? { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
Function Await($WinRtTask, $ResultType) {
    $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
    $netTask = $asTask.Invoke($null, @($WinRtTask))
    $netTask.Wait(-1) | Out-Null
    $netTask.Result
}

# Try to access UserNotificationListener
try {
    [Windows.UI.Notifications.Management.UserNotificationListener,Windows.UI.Notifications,ContentType=WindowsRuntime]
    $listener = [Windows.UI.Notifications.Management.UserNotificationListener]::GetDefault()
    Write-Output "Notification listener accessed"
} catch {
    Write-Output "Notification listener not available: $_"
}

# Broadcast settings change
$code = @'
[DllImport("user32.dll", CharSet=CharSet.Auto)]
public static extern IntPtr SendMessageTimeout(
    IntPtr hWnd, uint Msg, IntPtr wParam, string lParam,
    uint fuFlags, uint uTimeout, out IntPtr lpdwResult);
'@
$type = Add-Type -MemberDefinition $code -Name User32 -Namespace Win32Functions -PassThru
$HWND_BROADCAST = [IntPtr]0xffff
$WM_SETTINGCHANGE = 0x1a
$result = [IntPtr]::Zero
$type::SendMessageTimeout($HWND_BROADCAST, $WM_SETTINGCHANGE, [IntPtr]::Zero, "UserPreferences", 2, 5000, [ref]$result)
Write-Output "Settings change broadcasted"
'''
try:
    result = subprocess.run(
        ["powershell", "-ExecutionPolicy", "Bypass", "-Command", ps_command],
        capture_output=True,
        text=True,
        timeout=15,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    print(f"   PowerShell Output:\n{result.stdout}")
    if result.stderr:
        print(f"   PowerShell Errors:\n{result.stderr[:500]}")
except Exception as e:
    print(f"   [ERROR] PowerShell failed: {e}")

# Method 4: Restart notification-related services
print("\n4. Restarting Notification Services...")
restart_cmd = '''
Get-Process -Name "ShellExperienceHost" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Get-Process -Name "RuntimeBroker" -ErrorAction SilentlyContinue | Where-Object {$_.MainWindowTitle -eq ""} | Stop-Process -Force -ErrorAction SilentlyContinue
Write-Output "Notification services restarted"
'''
try:
    result = subprocess.run(
        ["powershell", "-Command", restart_cmd],
        capture_output=True,
        text=True,
        timeout=10,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    print(f"   {result.stdout.strip()}")
except Exception as e:
    print(f"   [WARNING] Service restart failed: {e}")

# Method 5: Verify final state
print("\n5. Final Verification:")
import time
time.sleep(1)
try:
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, qh_key, 0, winreg.KEY_READ) as key:
        val, _ = winreg.QueryValueEx(key, "FocusAssist")
        print(f"   Focus Assist: {val} {'[OK]' if val == 2 else '[NOT SET]'}")
except Exception as e:
    print(f"   [ERROR] Could not verify: {e}")

print("\n" + "=" * 60)
print("If notifications still appear:")
print("1. Some apps (Teams, Outlook, Discord) bypass Focus Assist")
print("2. Go to Settings > System > Focus Assist and manually toggle")
print("3. Check Settings > System > Notifications for app-specific settings")
print("4. You may need to disable notifications per-app")
print("=" * 60)


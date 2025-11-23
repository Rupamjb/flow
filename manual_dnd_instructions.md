# Manual DND Activation Instructions

Since Windows sometimes doesn't apply registry changes immediately, here's how to manually activate Focus Assist:

## Quick Method:
1. **Open Windows Settings**: Press `Win + I`
2. **Go to**: System > Focus Assist
3. **Set to**: "Alarms only"
4. **Verify**: Check the Action Center (bottom-right) - you should see the Focus Assist icon

## Alternative Method (Command Line):
Run this in PowerShell as Administrator:
```powershell
# Open Focus Assist settings
Start-Process "ms-settings:quiethours"
```

## Why Notifications May Still Appear:
1. **Some apps bypass Focus Assist**: Teams, Outlook, Discord, and some games can send notifications even with Focus Assist on
2. **Time-sensitive notifications**: Some apps mark notifications as "time-sensitive" which bypasses DND
3. **Windows requires manual toggle**: Sometimes Windows needs you to manually toggle Focus Assist for it to take effect

## To Block Specific Apps:
1. Go to: Settings > System > Notifications
2. Find the app that's sending notifications
3. Toggle it off individually

## Verify DND is Active:
- Look for the Focus Assist icon in the Action Center (bottom-right corner)
- It should show "Alarms only" when active
- If it shows "Off", you need to manually toggle it


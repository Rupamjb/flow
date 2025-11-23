"""
Windows Notification Suppressor
Disables notifications from specific applications during flow sessions.
Uses Windows Registry to control per-app notification settings.
"""

import winreg
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class NotificationSuppressor:
    """Manages Windows notification suppression for specific applications"""
    
    # Registry path for notification settings
    NOTIFICATIONS_KEY = r"Software\Microsoft\Windows\CurrentVersion\Notifications\Settings"
    
    # Common apps that send notifications (AppUserModelId or package names)
    DEFAULT_APPS = [
        # Microsoft Teams
        "Microsoft.Teams",
        "MicrosoftTeams",
        
        # Communication apps
        "Discord",
        "SlackTechnologies.Slack",
        "Slack",
        
        # Email clients
        "Microsoft.OutlookForWindows",
        "Microsoft.Office.Outlook",
        
        # Browsers (notifications from websites)
        "Google.Chrome",
        "Microsoft.Edge",
        "Mozilla.Firefox",
        
        # Other common apps
        "Microsoft.Windows.ShellExperienceHost",  # Windows notifications
        "Microsoft.WindowsStore",
        "SpotifyAB.SpotifyMusic",
        "Spotify",
        
        # Social media apps
        "Facebook.Facebook",
        "Twitter",
        "WhatsApp",
    ]
    
    def __init__(self, custom_apps: Optional[List[str]] = None):
        """
        Initialize the notification suppressor.
        
        Args:
            custom_apps: Optional list of additional app identifiers to suppress
        """
        self.suppressed_apps: List[str] = []
        self.original_states: Dict[str, int] = {}
        self.target_apps = self.DEFAULT_APPS.copy()
        
        if custom_apps:
            self.target_apps.extend(custom_apps)
    
    def get_notification_apps(self) -> List[str]:
        """
        Get list of apps that have notification settings in the registry.
        
        Returns:
            List of app identifiers found in notification settings
        """
        apps = []
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.NOTIFICATIONS_KEY, 0, winreg.KEY_READ) as key:
                index = 0
                while True:
                    try:
                        app_name = winreg.EnumKey(key, index)
                        apps.append(app_name)
                        index += 1
                    except OSError:
                        break
        except Exception as e:
            logger.error(f"Failed to enumerate notification apps: {e}")
        
        return apps
    
    def _get_app_notification_state(self, app_id: str) -> Optional[int]:
        """
        Get the current notification state for an app.
        
        Args:
            app_id: Application identifier
            
        Returns:
            Current Enabled value (0=disabled, 1=enabled) or None if not found
        """
        try:
            app_key_path = f"{self.NOTIFICATIONS_KEY}\\{app_id}"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, app_key_path, 0, winreg.KEY_READ) as key:
                try:
                    value, _ = winreg.QueryValueEx(key, "Enabled")
                    return int(value)
                except FileNotFoundError:
                    # If Enabled key doesn't exist, notifications are enabled by default
                    return 1
        except FileNotFoundError:
            # App key doesn't exist
            return None
        except Exception as e:
            logger.warning(f"Failed to read notification state for {app_id}: {e}")
            return None
    
    def _set_app_notification_state(self, app_id: str, enabled: int) -> bool:
        """
        Set the notification state for an app.
        
        Args:
            app_id: Application identifier
            enabled: 0 to disable, 1 to enable
            
        Returns:
            True if successful, False otherwise
        """
        try:
            app_key_path = f"{self.NOTIFICATIONS_KEY}\\{app_id}"
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, app_key_path) as key:
                winreg.SetValueEx(key, "Enabled", 0, winreg.REG_DWORD, enabled)
                return True
        except Exception as e:
            logger.error(f"Failed to set notification state for {app_id}: {e}")
            return False
    
    def suppress_notifications(self, app_list: Optional[List[str]] = None) -> Dict[str, bool]:
        """
        Disable notifications for specified apps.
        
        Args:
            app_list: Optional list of app identifiers. If None, uses target_apps.
            
        Returns:
            Dictionary mapping app_id to success status
        """
        if app_list is None:
            app_list = self.target_apps
        
        # Get all apps with notification settings
        available_apps = self.get_notification_apps()
        
        results = {}
        suppressed_count = 0
        
        for target_app in app_list:
            # Find matching apps (case-insensitive partial match)
            matching_apps = [
                app for app in available_apps 
                if target_app.lower() in app.lower()
            ]
            
            for app_id in matching_apps:
                # Skip if already suppressed
                if app_id in self.suppressed_apps:
                    continue
                
                # Get current state
                current_state = self._get_app_notification_state(app_id)
                
                if current_state is not None:
                    # Store original state
                    self.original_states[app_id] = current_state
                    
                    # Disable notifications
                    if self._set_app_notification_state(app_id, 0):
                        self.suppressed_apps.append(app_id)
                        results[app_id] = True
                        suppressed_count += 1
                        logger.info(f"✓ Suppressed notifications for: {app_id}")
                    else:
                        results[app_id] = False
                        logger.warning(f"✗ Failed to suppress notifications for: {app_id}")
        
        if suppressed_count > 0:
            logger.info(f"🔕 Notifications suppressed for {suppressed_count} app(s)")
        else:
            logger.warning("⚠️ No matching apps found to suppress notifications")
        
        return results
    
    def restore_notifications(self) -> Dict[str, bool]:
        """
        Restore original notification states for all suppressed apps.
        
        Returns:
            Dictionary mapping app_id to success status
        """
        results = {}
        restored_count = 0
        
        for app_id in self.suppressed_apps:
            original_state = self.original_states.get(app_id, 1)  # Default to enabled
            
            if self._set_app_notification_state(app_id, original_state):
                results[app_id] = True
                restored_count += 1
                logger.info(f"✓ Restored notifications for: {app_id}")
            else:
                results[app_id] = False
                logger.warning(f"✗ Failed to restore notifications for: {app_id}")
        
        if restored_count > 0:
            logger.info(f"🔔 Notifications restored for {restored_count} app(s)")
        
        # Clear tracking
        self.suppressed_apps.clear()
        self.original_states.clear()
        
        return results
    
    def get_status(self) -> Dict:
        """
        Get current suppression status.
        
        Returns:
            Dictionary with suppression status information
        """
        return {
            "is_suppressing": len(self.suppressed_apps) > 0,
            "suppressed_count": len(self.suppressed_apps),
            "suppressed_apps": self.suppressed_apps.copy(),
            "target_apps": self.target_apps.copy()
        }


# Test function
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("Windows Notification Suppressor - Test Mode")
    print("=" * 50)
    
    suppressor = NotificationSuppressor()
    
    print("\n1. Getting available notification apps...")
    apps = suppressor.get_notification_apps()
    print(f"Found {len(apps)} apps with notification settings:")
    for app in apps[:10]:  # Show first 10
        state = suppressor._get_app_notification_state(app)
        status = "Enabled" if state == 1 else "Disabled" if state == 0 else "Unknown"
        print(f"  - {app}: {status}")
    
    print("\n2. Testing suppression...")
    results = suppressor.suppress_notifications()
    print(f"Suppression results: {len([r for r in results.values() if r])} successful")
    
    print("\n3. Current status:")
    status = suppressor.get_status()
    print(f"  Suppressing: {status['is_suppressing']}")
    print(f"  Apps suppressed: {status['suppressed_count']}")
    
    input("\nPress Enter to restore notifications...")
    
    print("\n4. Restoring notifications...")
    restore_results = suppressor.restore_notifications()
    print(f"Restoration results: {len([r for r in restore_results.values() if r])} successful")
    
    print("\nTest complete!")

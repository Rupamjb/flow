"""
CRITICAL SAFETY NET - Registry Installer for Native Messaging Host
This script MUST be run before the Chrome extension will work.
Without this, Chrome will fail with "Native host has exited" error.
"""

import os
import sys
import winreg
from pathlib import Path
import json

def install_native_host(ext_id: str | None = None):
    """Install the native messaging host registry key for 'com.flow.engine'"""
    # Get absolute paths
    extension_dir = Path(__file__).parent.absolute()
    # Use the host manifest that matches background.js hostName
    manifest_path = extension_dir / "host_manifest.json"
    bridge_path = extension_dir / "bridge.py"
    
    # Verify files exist
    if not manifest_path.exists():
        print(f"❌ ERROR: Manifest not found at {manifest_path}")
        return False
    
    if not bridge_path.exists():
        print(f"❌ ERROR: Bridge script not found at {bridge_path}")
        return False
    
    # Update manifest with correct Python path
    print(f"📝 Updating manifest with absolute paths...")
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    # Set the correct path using a .bat wrapper that calls current Python
    python_exe = sys.executable
    bat_wrapper = extension_dir / "bridge.bat"
    with open(bat_wrapper, 'w') as f:
        f.write(f'@echo off\n"{python_exe}" "{bridge_path}" %*\n')
    # Update manifest path to wrapper
    manifest["path"] = str(bat_wrapper)
    # Optionally update allowed_origins with provided extension ID
    if ext_id:
        manifest["allowed_origins"] = [f"chrome-extension://{ext_id}/"]
    
    # Save updated manifest
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"✅ Updated manifest: {manifest_path}")
    
    # Registry key path must match background.js hostName
    registry_path = r"Software\Google\Chrome\NativeMessagingHosts\com.flow.engine"
    
    try:
        # Create/open registry key
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, registry_path)
        
        # Set the default value to the manifest path
        winreg.SetValue(key, "", winreg.REG_SZ, str(manifest_path))
        
        winreg.CloseKey(key)
        
        print("=" * 70)
        print("✅ SUCCESS! Native messaging host registered!")
        print("=" * 70)
        print(f"📍 Registry Key: HKCU\\{registry_path}")
        print(f"📄 Manifest Path: {manifest_path}")
        print(f"🐍 Bridge Script: {bridge_path}")
        print(f"🦇 Wrapper Script: {bat_wrapper}")
        print("=" * 70)
        print("\n📋 NEXT STEPS:")
        print("1. Open Chrome and go to chrome://extensions/")
        print("2. Enable 'Developer mode' (top right)")
        print("3. Click 'Load unpacked' and select:")
        print(f"   {extension_dir}")
        print("4. Note the Extension ID from the extension card")
        print("5. Update native_host_manifest.json with the Extension ID")
        print("6. Run this script again to update the registry")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: Failed to write registry key: {e}")
        print("💡 TIP: Try running as Administrator")
        return False

def verify_installation():
    """Verify the registry key is correctly set for 'com.flow.engine'"""
    registry_path = r"Software\Google\Chrome\NativeMessagingHosts\com.flow.engine"
    
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_path)
        manifest_path = winreg.QueryValue(key, "")
        winreg.CloseKey(key)
        
        print(f"✅ Registry key exists: {manifest_path}")
        
        if Path(manifest_path).exists():
            print(f"✅ Manifest file exists")
            return True
        else:
            print(f"❌ Manifest file not found at registered path")
            return False
            
    except FileNotFoundError:
        print(f"❌ Registry key not found: HKCU\\{registry_path}")
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("🔧 Flow State Facilitator - Native Host Installer")
    print("=" * 70)
    print()
    
    # Check if verifying or installing
    if len(sys.argv) > 1 and sys.argv[1] == "--verify":
        verify_installation()
    else:
        ext_id = None
        # Support: install_host.py --ext-id ABCDEF... (without braces)
        if len(sys.argv) > 2 and sys.argv[1] == "--ext-id":
            ext_id = sys.argv[2]
        install_native_host(ext_id)

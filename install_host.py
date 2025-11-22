"""
Flow State Facilitator - Native Messaging Installer
Registers the Python bridge script as a Native Messaging Host in the Windows Registry.
"""

import sys
import os
import json
import winreg
from pathlib import Path

# Configuration
HOST_NAME = "com.flow.engine"
ALLOWED_ORIGINS = [
    "chrome-extension://YOUR_EXTENSION_ID_HERE/"  # TODO: User needs to update this after loading extension
]

def install_host():
    """Install the Native Messaging Host manifest and registry key"""
    
    # 1. Locate the bridge script
    current_dir = Path(__file__).parent.absolute()
    bridge_script = current_dir / "extension" / "bridge.py"
    manifest_path = current_dir / "extension" / "host_manifest.json"
    
    if not bridge_script.exists():
        print(f"❌ Error: bridge.py not found at {bridge_script}")
        return
    
    # 2. Create the Host Manifest
    # Windows requires the path to be the executable (python) and args
    python_exe = sys.executable
    
    manifest = {
        "name": HOST_NAME,
        "description": "Flow State Facilitator Bridge",
        "path": python_exe,
        "args": [str(bridge_script)],
        "type": "stdio",
        "allowed_origins": ALLOWED_ORIGINS
    }
    
    print(f"📝 Creating manifest at {manifest_path}...")
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
        
    # 3. Write to Windows Registry
    key_path = f"SOFTWARE\\Google\\Chrome\\NativeMessagingHosts\\{HOST_NAME}"
    
    try:
        # Try writing to HKEY_CURRENT_USER
        print(f"🔑 Writing registry key: HKCU\\{key_path}")
        reg_key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
        winreg.SetValueEx(reg_key, "", 0, winreg.REG_SZ, str(manifest_path))
        winreg.CloseKey(reg_key)
        print("✅ Registry key created successfully!")
        
    except Exception as e:
        print(f"❌ Failed to write registry key: {e}")
        print("Try running as Administrator.")
        return

    print("\n" + "="*60)
    print("🎉 INSTALLATION COMPLETE")
    print("="*60)
    print("IMPORTANT NEXT STEPS:")
    print("1. Load the 'extension' folder in Chrome (chrome://extensions)")
    print("2. Copy the generated Extension ID (e.g., 'abcdefghijklmnop...')")
    print("3. Update the 'ALLOWED_ORIGINS' list in 'extension/host_manifest.json'")
    print("   with: 'chrome-extension://<YOUR_ID>/'")
    print("4. Restart Chrome")
    print("="*60)

if __name__ == "__main__":
    install_host()

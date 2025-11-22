import sys
import os
import json
import struct
import subprocess
import time
from pathlib import Path

# Path to the bridge script
BRIDGE_SCRIPT = Path(__file__).parent.parent / "extension" / "bridge.py"

def test_bridge():
    print(f"Testing bridge script at: {BRIDGE_SCRIPT}")
    
    # Start the bridge process
    # We need to set PYTHONUNBUFFERED to ensure we get output immediately
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    
    process = subprocess.Popen(
        [sys.executable, str(BRIDGE_SCRIPT)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env
    )
    
    try:
        # Prepare a test message
        message = {
            "type": "browser_activity",
            "url": "https://www.google.com",
            "title": "Google",
            "timestamp": time.time()
        }
        
        encoded_msg = json.dumps(message).encode('utf-8')
        length_bytes = struct.pack('I', len(encoded_msg))
        
        print("Sending message to bridge...")
        process.stdin.write(length_bytes)
        process.stdin.write(encoded_msg)
        process.stdin.flush()
        
        # Read response
        # First 4 bytes should be length
        print("Waiting for response...")
        response_len_bytes = process.stdout.read(4)
        
        if not response_len_bytes:
            print("❌ No response received (process might have crashed)")
            stderr = process.stderr.read().decode()
            if stderr:
                print(f"STDERR: {stderr}")
            return False
            
        response_len = struct.unpack('I', response_len_bytes)[0]
        response_bytes = process.stdout.read(response_len)
        response = json.loads(response_bytes.decode('utf-8'))
        
        print(f"✅ Received response: {response}")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        process.terminate()

if __name__ == "__main__":
    success = test_bridge()
    sys.exit(0 if success else 1)

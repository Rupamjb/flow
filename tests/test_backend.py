import sys
import os
import time
import requests
import subprocess
from pathlib import Path

# Path to main.py
BACKEND_SCRIPT = Path(__file__).parent.parent / "backend" / "main.py"

def wait_for_server(url, timeout=10):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            requests.get(url)
            return True
        except requests.ConnectionError:
            time.sleep(0.5)
    return False

def test_backend():
    print(f"Testing backend at: {BACKEND_SCRIPT}")
    
    # Start the backend server
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    
    process = subprocess.Popen(
        [sys.executable, str(BACKEND_SCRIPT)],
        cwd=str(BACKEND_SCRIPT.parent),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env
    )
    
    try:
        base_url = "http://127.0.0.1:8000"
        print("Waiting for server to start...")
        
        if not wait_for_server(f"{base_url}/api/health"):
            print("❌ Server failed to start")
            # Read output to see why
            out, err = process.communicate(timeout=1)
            print(f"STDOUT: {out.decode()}")
            print(f"STDERR: {err.decode()}")
            return False
            
        print("✅ Server is running")
        
        # Test 1: Health Check
        resp = requests.get(f"{base_url}/api/health")
        assert resp.status_code == 200
        print("✅ Health check passed")
        
        # Test 2: Status
        resp = requests.get(f"{base_url}/api/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "is_running" in data
        print("✅ Status endpoint passed")
        
        # Test 3: Start Session
        resp = requests.post(f"{base_url}/api/session/start")
        assert resp.status_code == 200
        print("✅ Start session passed")
        
        # Test 4: Browser Activity (Mock)
        activity = {
            "url": "https://example.com",
            "title": "Example",
            "timestamp": time.time()
        }
        resp = requests.post(f"{base_url}/api/activity/browser", json=activity)
        assert resp.status_code == 200
        print("✅ Browser activity passed")
        
        # Test 5: Stop Session
        resp = requests.post(f"{base_url}/api/session/stop")
        assert resp.status_code == 200
        print("✅ Stop session passed")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        print("Stopping server...")
        process.terminate()
        process.wait()

if __name__ == "__main__":
    success = test_backend()
    sys.exit(0 if success else 1)

"""
Flow State Facilitator - Native Messaging Bridge
Connects Chrome Extension to FastAPI server using binary stdio protocol.
CRITICAL: Uses msvcrt.setmode for Windows binary mode.
"""

import sys
import os
import json
import struct
import logging
import traceback
from pathlib import Path

# Setup logging immediately
LOG_FILE = Path(__file__).parent / "bridge.log"
logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def setup_windows_binary_mode():
    """Set binary mode for Windows stdio"""
    if sys.platform == "win32":
        try:
            import msvcrt
            msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
            msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
            logging.info("Binary mode set successfully")
        except Exception as e:
            logging.error(f"Failed to set binary mode: {e}")

def send_message(message: dict):
    """Send message to Chrome extension using native messaging protocol"""
    try:
        encoded_message = json.dumps(message).encode('utf-8')
        message_length = struct.pack('I', len(encoded_message))
        
        # Write to stdout in binary mode
        sys.stdout.buffer.write(message_length)
        sys.stdout.buffer.write(encoded_message)
        sys.stdout.buffer.flush()
        
        logging.debug(f"Sent message to Chrome: {message}")
    except Exception as e:
        logging.error(f"Error sending message: {e}")

def read_message():
    """Read message from Chrome extension"""
    try:
        # Read message length (4 bytes)
        raw_length = sys.stdin.buffer.read(4)
        
        if len(raw_length) == 0:
            logging.info("No more messages (stdin closed)")
            return None
        
        message_length = struct.unpack('I', raw_length)[0]
        
        # Read message content
        message_bytes = sys.stdin.buffer.read(message_length)
        message = json.loads(message_bytes.decode('utf-8'))
        
        logging.debug(f"Received message from Chrome: {message}")
        return message
        
    except Exception as e:
        logging.error(f"Error reading message: {e}")
        return None

def forward_to_fastapi(message: dict):
    """Forward message to FastAPI server"""
    try:
        import httpx
        
        # Determine endpoint based on message type
        if message.get("type") == "browser_activity":
            endpoint = "http://127.0.0.1:8000/api/activity/browser"
            data = {
                "url": message.get("url", ""),
                "title": message.get("title", ""),
                "timestamp": message.get("timestamp", 0)
            }
        elif message.get("type") == "search_query":
            endpoint = "http://127.0.0.1:8000/api/activity/query"
            data = {
                "query": message.get("query", ""),
                "engine": message.get("engine", ""),
                "timestamp": message.get("timestamp", 0)
            }
        else:
            logging.warning(f"Unknown message type: {message.get('type')}")
            return {"status": "error", "message": "Unknown message type"}
        
        # Send to FastAPI
        response = httpx.post(endpoint, json=data, timeout=5.0)
        result = response.json()
        
        logging.info(f"FastAPI response: {result}")
        return result
        
    except ImportError:
        logging.error("httpx module not found. Please install it.")
        return {"status": "error", "message": "httpx module missing"}
    except Exception as e:
        logging.error(f"Error forwarding to FastAPI: {e}")
        return {"status": "error", "message": str(e)}

def main():
    """Main bridge loop"""
    logging.info("=" * 60)
    logging.info("🌉 Native Messaging Bridge Started")
    logging.info("=" * 60)
    
    setup_windows_binary_mode()
    
    try:
        while True:
            # Read message from Chrome
            message = read_message()
            
            if message is None:
                break
            
            # Forward to FastAPI and get response
            response = forward_to_fastapi(message)
            
            # Send response back to Chrome
            send_message(response)
            
    except KeyboardInterrupt:
        logging.info("Bridge stopped by user")
    except Exception as e:
        logging.error(f"Fatal error in bridge: {e}")
        logging.error(traceback.format_exc())
    finally:
        logging.info("Bridge shutting down")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Last resort logging
        with open("bridge_fatal_error.log", "w") as f:
            f.write(str(e))
            f.write(traceback.format_exc())


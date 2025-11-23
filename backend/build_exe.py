import PyInstaller.__main__
import os
import sys

# Define base directory
base_dir = os.path.dirname(os.path.abspath(__file__))

# Define frontend dist path
frontend_dist = os.path.join(os.path.dirname(base_dir), 'frontend-react', 'dist')

# Verify frontend build exists
if not os.path.exists(frontend_dist):
    print(f"ERROR: Frontend build not found at {frontend_dist}")
    print("Please run 'npm run build' in the frontend-react directory first.")
    sys.exit(1)

# Define arguments
args = [
    'desktop_app.py',
    '--name=FlowEngine',
    '--noconsole',
    '--clean',
    '--noconfirm',
    
    # Add data files (format: source;dest for Windows)
    f'--add-data={frontend_dist};frontend-react/dist',
    f'--add-data={os.path.join(os.path.dirname(base_dir), "user_config.json")};.',
    f'--add-data={os.path.join(os.path.dirname(base_dir), ".env")};.',
    
    # Hidden imports
    '--hidden-import=uvicorn.logging',
    '--hidden-import=uvicorn.loops',
    '--hidden-import=uvicorn.loops.auto',
    '--hidden-import=uvicorn.protocols',
    '--hidden-import=uvicorn.protocols.http',
    '--hidden-import=uvicorn.protocols.http.auto',
    '--hidden-import=uvicorn.protocols.websockets',
    '--hidden-import=uvicorn.protocols.websockets.auto',
    '--hidden-import=uvicorn.lifespan.on',
    '--hidden-import=engineio.async_drivers.asgi',
    '--hidden-import=engineio.async_drivers.threading',
    '--hidden-import=socketio.async_drivers.asgi',
    '--hidden-import=socketio.async_drivers.threading',
    '--hidden-import=fastapi',
    '--hidden-import=starlette',
    '--hidden-import=pydantic',
    '--hidden-import=dotenv',
    '--hidden-import=requests',
    '--hidden-import=psutil',
    '--hidden-import=webview',
    '--hidden-import=clr',
]

# Run PyInstaller
print("Starting PyInstaller build...")
PyInstaller.__main__.run(args)
print("Build complete! Check the 'dist' folder.")

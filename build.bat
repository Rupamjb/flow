@echo off
echo Stopping running instances...
taskkill /F /IM FlowEngine.exe /T 2>nul

echo Cleaning previous build...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del *.spec

echo Installing/Upgrading Build Tools...
pip uninstall -y setuptools
pip install setuptools==65.5.0 wheel pyinstaller

echo Building Flow Engine...
pyinstaller --noconsole --onedir --name "FlowEngine" --hidden-import=pkg_resources.py2_warn --add-data "backend/onboarding.py;." --add-data "extension/icon48.png;extension" backend/launcher.py

echo Build Complete!
echo Executable is located in dist/FlowEngine/FlowEngine.exe
pause

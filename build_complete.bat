@echo off
echo ============================================
echo Flow Engine - Complete Build Script
echo ============================================
echo.

REM Kill any running instances
echo Stopping any running instances...
taskkill /F /IM FlowEngine.exe /T 2>nul
taskkill /F /IM python.exe /T 2>nul
timeout /t 2 /nobreak >nul

REM Clean previous builds
echo Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del *.spec

REM Upgrade build tools
echo Upgrading build tools...
python -m pip install --upgrade pip
pip uninstall -y setuptools
pip install setuptools==65.5.0 wheel pyinstaller

REM Install all dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Create requirements.txt if it doesn't exist
if not exist requirements.txt (
    echo Creating requirements.txt...
    pip freeze > requirements.txt
)

REM Build with PyInstaller
echo.
echo ============================================
echo Building FlowEngine.exe...
echo ============================================
echo.

pyinstaller --noconsole ^
    --onedir ^
    --name "FlowEngine" ^
    --icon="extension/icon48.png" ^
    --add-data "backend/onboarding.py;." ^
    --add-data "backend/main.py;." ^
    --add-data "backend/database.py;." ^
    --add-data "backend/window_monitor.py;." ^
    --add-data "backend/interventions.py;." ^
    --add-data "backend/blocker.py;." ^
    --add-data "backend/input_monitor.py;." ^
    --add-data "backend/soft_reset.py;." ^
    --add-data "backend/local_db.py;." ^
    --add-data "backend/pattern_analyzer.py;." ^
    --add-data "backend/ai_classifier.py;." ^
    --add-data "extension/icon48.png;extension" ^
    --add-data ".env;." ^
    --hidden-import=backports ^
    --hidden-import=pynput ^
    --hidden-import=pycaw ^
    --hidden-import=requests ^
    --hidden-import=dotenv ^
    --hidden-import=sqlite3 ^
    --hidden-import=multiprocessing ^
    --collect-all=backports ^
    --collect-all=pynput ^
    --collect-all=pycaw ^
    backend/launcher.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ============================================
    echo BUILD FAILED!
    echo ============================================
    pause
    exit /b 1
)

echo.
echo ============================================
echo BUILD SUCCESSFUL!
echo ============================================
echo.
echo Executable location: dist\FlowEngine\FlowEngine.exe
echo.
echo To run: cd dist\FlowEngine && FlowEngine.exe
echo.
pause

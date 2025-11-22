@echo off
echo ============================================
echo Flow Engine - Quick UI Fix Build
echo ============================================
echo.
echo This rebuilds with --windowed instead of --noconsole
echo to show the Tkinter UI properly.
echo.

REM Kill any running instances
taskkill /F /IM FlowEngine.exe /T 2>nul
taskkill /F /IM python.exe /T 2>nul
timeout /t 2 /nobreak >nul

REM Clean previous builds
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del *.spec

echo Building with UI support...
echo.

pyinstaller --windowed ^
    --onedir ^
    --name "FlowEngine" ^
    --icon="extension/icon48.png" ^
    --add-data "backend;backend" ^
    --add-data "extension/icon48.png;extension" ^
    --add-data ".env;." ^
    --hidden-import=pynput ^
    --hidden-import=pycaw ^
    --hidden-import=requests ^
    --hidden-import=dotenv ^
    --hidden-import=multiprocessing ^
    --collect-all=pynput ^
    --collect-all=pycaw ^
    backend/launcher.py

if %ERRORLEVEL% NEQ 0 (
    echo BUILD FAILED!
    pause
    exit /b 1
)

echo.
echo ============================================
echo BUILD SUCCESSFUL!
echo ============================================
echo.
echo The UI will now show when you run FlowEngine.exe
echo Location: dist\FlowEngine\FlowEngine.exe
echo.
pause

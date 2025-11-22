# Flow State Facilitator

A Windows-based AI productivity tool that detects when you enter a "Flow State" (deep work) and actively protects it using intelligent distraction blocking and RPG-style gamification.

## 🎯 Features

- **Tri-Layer Flow Detection**: Monitors app usage, browser context, and input patterns
- **Smart Blocking**: Overlay intercepts instead of killing processes
- **Micro-Interventions**: Gentle cognitive fatigue resets with blur and audio fade
- **RPG Gamification**: Track Stamina, Resilience, and Consistency stats
- **Progressive Overload**: AI-driven focus duration training
- **Watchdog Resilience**: Auto-restart system for maximum uptime

## 🚀 Quick Start

### Prerequisites

- Windows 10/11
- Python 3.8+
- Google Chrome

### Installation

1. **Clone or download this repository**

2. **Install Python dependencies**
   ```bash
   cd d:\flow\backend
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your Supabase credentials (optional for hackathon demo)
   ```

4. **Install Chrome Extension Native Messaging Host** (CRITICAL)
   ```bash
   cd d:\flow\extension
   python install_host.py
   ```
   This writes the required Windows registry key for Chrome to communicate with the backend.

5. **Load Chrome Extension**
   - Open Chrome and navigate to `chrome://extensions/`
   - Enable "Developer mode" (top right)
   - Click "Load unpacked"
   - Select the `d:\flow\extension` folder
   - Note the Extension ID shown on the extension card

6. **Update Extension ID in manifest**
   - Open `d:\flow\extension\native_host_manifest.json`
   - Replace `EXTENSION_ID_PLACEHOLDER` with your actual Extension ID
   - Run `python install_host.py` again to update the registry

7. **Start the backend server**
   ```bash
   cd d:\flow\backend
   python main.py
   ```

8. **Start the watchdog** (optional, for resilience)
   ```bash
   # In a new terminal
   cd d:\flow\backend
   python watchdog.py
   ```

9. **Open the dashboard**
   - Navigate to http://localhost:8000

## 📁 Project Structure

```
d:\flow\
├── backend\
│   ├── main.py              # FastAPI server (the brain)
│   ├── watchdog.py          # Process resilience monitor
│   ├── window_monitor.py    # Win32 API window tracking
│   ├── interventions.py     # Micro-interventions (blur, audio)
│   └── requirements.txt     # Python dependencies
├── extension\
│   ├── manifest.json        # Chrome extension config
│   ├── background.js        # Tab monitoring service
│   ├── bridge.py            # Native messaging host
│   ├── install_host.py      # Registry installer (CRITICAL)
│   ├── native_host_manifest.json
│   ├── popup.html           # Extension popup UI
│   └── popup.js
├── frontend\
│   ├── index.html           # Dashboard UI
│   ├── styles.css           # Glassmorphism design
│   └── app.js               # Real-time updates
└── .env.example             # Environment template
```

## 🔧 How It Works

### Flow Detection (Tri-Layer System)

1. **Layer 1 - App Usage**: Monitors active window titles via Win32 API
2. **Layer 2 - Context**: Chrome extension reads active URLs to distinguish productive vs. distracting sites
3. **Layer 3 - Cadence**: Analyzes input patterns (keyboard/mouse activity) to detect engagement

When all three layers indicate focused work for 10+ minutes (configurable), flow state is triggered.

### Blocking Mechanism

Instead of killing processes, the system uses an **Overlay Intercept**:
- When a distraction app opens during flow, a full-screen topmost overlay appears
- Shows message: "You are in Flow. Break it?"
- 10-second countdown before "Unlock" button activates
- Builds resilience by making you consciously choose to break flow

### Micro-Interventions

When cognitive fatigue is detected:
- **Screen Blur**: Transparent overlay with blur effect
- **Audio Fade**: Linear cross-fade volume reduction (not abrupt)
- Gentle nudge to take a break without disrupting flow completely

### RPG Stats

- **Stamina**: Total minutes spent in flow state
- **Resilience**: Number of times you resisted the overlay
- **Consistency**: Daily streak counter

## 🧪 Testing

### Test Flow Detection
```bash
# Open a focus app (VS Code, PyCharm, etc.)
# Work for 10+ minutes
# Check dashboard - should show "In Flow State"
```

### Test Distraction Blocking
```bash
# While in flow, open Steam or Instagram
# Should see console log: "🚫 OVERLAY TRIGGERED"
# (Full overlay UI is simplified for hackathon)
```

### Test Watchdog
```bash
# Start main.py
# Start watchdog.py
# Kill main.py process
# Watchdog should restart it within 5 seconds
```

### Test Chrome Extension
```bash
# Check Chrome extension console (chrome://extensions/ > Details > Inspect views: service worker)
# Should see: "✅ Connected to native host"
# Visit different websites - should see messages being sent
```

## 🐛 Troubleshooting

### "Native host has exited" error
- Run `python install_host.py` in the extension folder
- Verify registry key exists: `HKCU\Software\Google\Chrome\NativeMessagingHosts\com.flowstate.extension`
- Check that Extension ID in `native_host_manifest.json` matches your actual extension ID

### Server won't start
- Check if port 8000 is already in use
- Verify all dependencies are installed: `pip install -r requirements.txt`
- On Windows, you may need to install pywin32 manually: `pip install pywin32`

### Window monitoring not working
- Ensure pywin32 is installed correctly
- May need to run: `python Scripts/pywin32_postinstall.py -install` (in your Python installation)

## 📊 API Endpoints

- `GET /` - Dashboard UI
- `GET /api/status` - Current flow state status
- `GET /api/stats` - RPG stats
- `GET /api/sessions` - Session history
- `POST /api/activity/window` - Report window activity
- `POST /api/activity/browser` - Report browser context
- `POST /api/flow/break` - Manually break flow
- `POST /api/overlay/resist` - User resisted overlay
- `GET /api/health` - Health check for watchdog

Full API documentation: http://localhost:8000/docs

## 🎨 Tech Stack

- **Backend**: FastAPI, Python 3.8+
- **OS Integration**: pywin32, psutil
- **Database**: Supabase (optional, async sync)
- **Frontend**: HTML/CSS/JavaScript (Vanilla)
- **Browser**: Chrome Extension (Manifest V3)
- **Native Messaging**: Binary stdio protocol

## 🏆 Hackathon Notes

This is a working demo built for speed. Production enhancements would include:
- Full overlay window implementation (currently console-only)
- Advanced AI heuristics for flow detection
- Complete progressive overload algorithm
- Timetable import and fluid goals
- Mobile app integration
- Multi-monitor support

## 📝 License

MIT License - Hackathon Project

## 👥 Credits

Built for the AI Productivity Tools Hackathon

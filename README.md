# Flow Engine 🌊

**The Neuro-Productivity System for Deep Work**

Flow Engine is an intelligent desktop application designed to help you achieve and maintain a state of "Flow". It combines AI-powered insights, distraction blocking, and gamification to optimize your productivity.

![Flow Engine UI](https://via.placeholder.com/800x400?text=Flow+Engine+Dashboard)

## 🚀 Features

-   **🧠 AI-Powered Insights**: Analyzes your work patterns to provide personalized tips on how to improve your focus and flow state.
-   **🛡️ Smart Distraction Blocking**: Automatically suppresses notifications (Discord, Teams, Slack, etc.) and blocks distracting websites/apps during flow sessions.
-   **📊 Analytics & Metrics**: Tracks your Focus Score, XP gained, and flow duration over time.
-   **🎮 Gamification**: Earn XP, level up your "Resilience" and "Stamina", and compete with your past self.
-   **🐕 Watchdog Protection**: A resilience penalty system discourages forceful termination of the app, keeping you accountable.
-   **🖥️ Desktop Overlay**: A non-intrusive overlay keeps you aware of your current state without breaking immersion.

## 🛠️ Tech Stack

-   **Backend**: Python (FastAPI), Supabase (Database)
-   **Frontend**: React, Vite, TailwindCSS
-   **AI**: Groq API (Llama 3.1)
-   **Desktop Integration**: Pywebview, PyInstaller, Windows Registry (for notifications)

## 📦 Installation

### Prerequisites
-   Python 3.8+
-   Node.js 16+

### Setup

1.  **Clone the repository**
    ```bash
    git clone https://github.com/yourusername/flow-engine.git
    cd flow-engine
    ```

2.  **Backend Setup**
    ```bash
    cd backend
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

3.  **Frontend Setup**
    ```bash
    cd ../frontend-react
    npm install
    npm run build
    ```

4.  **Configuration**
    -   Create a `.env` file in the root directory with your API keys (Groq, Supabase).
    -   (Optional) Customize `user_config.json` for your preferences.

## 🏃 Usage

### Running from Source
1.  Start the backend:
    ```bash
    cd backend
    python main.py
    ```
2.  Start the frontend (dev mode):
    ```bash
    cd frontend-react
    npm run dev
    ```

### Running the Standalone App
1.  Navigate to `backend/dist/FlowEngine`
2.  Run `FlowEngine.exe`

## 🏗️ Building the Executable

To package the application into a single executable:

1.  Build the frontend:
    ```bash
    cd frontend-react
    npm run build
    ```
2.  Build the backend executable:
    ```bash
    cd backend
    python build_exe.py
    ```
3.  The output will be in `backend/dist/FlowEngine`.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

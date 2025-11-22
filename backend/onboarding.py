"""
Flow State Facilitator - Onboarding Module
A simple Tkinter GUI to capture user's daily timetable and habits.
Saves configuration to 'user_config.json'.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from pathlib import Path

CONFIG_FILE = Path(__file__).parent.parent / "user_config.json"

class OnboardingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Flow Engine - Initial Setup")
        self.root.geometry("500x600")
        self.root.configure(bg="#0a0a0a")
        
        # Cyberpunk Style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("TLabel", background="#0a0a0a", foreground="#ffffff", font=("Segoe UI", 10))
        self.style.configure("TButton", background="#219ebc", foreground="#ffffff", font=("Segoe UI", 10, "bold"))
        self.style.map("TButton", background=[('active', '#ffb703')])
        self.style.configure("TEntry", fieldbackground="#333333", foreground="#ffffff")
        
        self._create_widgets()
        
    def _create_widgets(self):
        # Header
        header = tk.Label(
            self.root, 
            text="WELCOME TO THE FLOW", 
            font=("Segoe UI", 20, "bold"),
            bg="#0a0a0a", 
            fg="#219ebc"
        )
        header.pack(pady=20)
        
        subtext = tk.Label(
            self.root,
            text="Let's calibrate your baseline.",
            font=("Segoe UI", 12),
            bg="#0a0a0a",
            fg="#888888"
        )
        subtext.pack(pady=(0, 20))
        
        # Container
        frame = tk.Frame(self.root, bg="#0a0a0a", padx=20)
        frame.pack(fill="both", expand=True)
        
        # 1. Timetable
        tk.Label(frame, text="DAILY DEEP WORK SCHEDULE", bg="#0a0a0a", fg="#ffb703", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(10, 5))
        
        time_frame = tk.Frame(frame, bg="#0a0a0a")
        time_frame.pack(fill="x")
        
        tk.Label(time_frame, text="Start (HH:MM):", bg="#0a0a0a", fg="#ffffff").pack(side="left")
        self.start_time = ttk.Entry(time_frame, width=10)
        self.start_time.insert(0, "09:00")
        self.start_time.pack(side="left", padx=10)
        
        tk.Label(time_frame, text="End (HH:MM):", bg="#0a0a0a", fg="#ffffff").pack(side="left")
        self.end_time = ttk.Entry(time_frame, width=10)
        self.end_time.insert(0, "17:00")
        self.end_time.pack(side="left", padx=10)
        
        # 2. Productive Apps
        tk.Label(frame, text="PRODUCTIVE APPS (Comma separated)", bg="#0a0a0a", fg="#ffb703", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(20, 5))
        self.productive_apps = ttk.Entry(frame, width=50)
        self.productive_apps.insert(0, "code, visual studio, docs, canvas, obsidian")
        self.productive_apps.pack(fill="x")
        
        # 3. Distracting Apps
        tk.Label(frame, text="DISTRACTING APPS (Comma separated)", bg="#0a0a0a", fg="#d00000", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(20, 5))
        self.distracting_apps = ttk.Entry(frame, width=50)
        self.distracting_apps.insert(0, "netflix, twitter, instagram, steam, discord")
        self.distracting_apps.pack(fill="x")
        
        # 4. Baseline
        tk.Label(frame, text="BASELINE FOCUS (Minutes)", bg="#0a0a0a", fg="#ffffff", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(20, 5))
        self.baseline = ttk.Scale(frame, from_=10, to=60, orient="horizontal")
        self.baseline.set(25)
        self.baseline.pack(fill="x")
        
        # Save Button
        btn_frame = tk.Frame(self.root, bg="#0a0a0a", pady=30)
        btn_frame.pack(fill="x")
        
        save_btn = tk.Button(
            btn_frame,
            text="INITIALIZE SYSTEM",
            font=("Segoe UI", 12, "bold"),
            bg="#219ebc",
            fg="#ffffff",
            activebackground="#ffb703",
            relief="flat",
            command=self.save_config
        )
        save_btn.pack(ipadx=20, ipady=10)
        
    def save_config(self):
        config = {
            "schedule": {
                "start": self.start_time.get(),
                "end": self.end_time.get()
            },
            "productive_keywords": [x.strip().lower() for x in self.productive_apps.get().split(",")],
            "distracting_keywords": [x.strip().lower() for x in self.distracting_apps.get().split(",")],
            "baseline_minutes": int(self.baseline.get()),
            "initialized": True
        }
        
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f, indent=4)
            
            messagebox.showinfo("Success", "Configuration saved.\nThe Flow Engine is ready.")
            self.root.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save config: {e}")

def run_onboarding():
    """Run the onboarding GUI"""
    if CONFIG_FILE.exists():
        # Check if already initialized
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                if data.get("initialized"):
                    print("✅ System already initialized.")
                    return
        except:
            pass
            
    root = tk.Tk()
    app = OnboardingApp(root)
    root.mainloop()

if __name__ == "__main__":
    run_onboarding()

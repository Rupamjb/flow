"""
Flow Engine - Local Database
SQLite-based local storage for pattern recognition and historical analysis.
Replaces cloud dependency with privacy-first local learning.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import logging

logger = logging.getLogger("FlowEngine.LocalDB")

# Database path
DB_PATH = Path(__file__).parent.parent / "flow_patterns.db"

class LocalDatabase:
    """Local SQLite database for pattern storage"""
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.conn = None
        self._init_db()
    
    def _init_db(self):
        """Initialize database and create tables"""
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        cursor = self.conn.cursor()
        
        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                duration_seconds INTEGER,
                focus_score REAL,
                fatigue_score REAL,
                apm_average REAL,
                distraction_count INTEGER DEFAULT 0,
                resilience_score INTEGER DEFAULT 0,
                stamina_score INTEGER DEFAULT 0,
                xp_total INTEGER,
                xp_breakdown TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # App patterns table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS app_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                app_name TEXT NOT NULL UNIQUE,
                total_time_seconds INTEGER DEFAULT 0,
                flow_breaks INTEGER DEFAULT 0,
                productive_sessions INTEGER DEFAULT 0,
                distraction_sessions INTEGER DEFAULT 0,
                last_used TIMESTAMP,
                is_blocked BOOLEAN DEFAULT 0,
                auto_blocked BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Flow windows table (biological patterns)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS flow_windows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                hour INTEGER NOT NULL,
                flow_quality REAL,
                apm_average REAL,
                duration_minutes INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date, hour)
            )
        """)
        
        # Activity log table (detailed tracking)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                timestamp TIMESTAMP NOT NULL,
                app_name TEXT,
                url TEXT,
                activity_type TEXT,
                apm REAL,
                fatigue_score REAL,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
        """)
        
        self.conn.commit()
        logger.info(f"Database initialized at {self.db_path}")
    
    # ========================================================================
    # SESSION MANAGEMENT
    # ========================================================================
    
    def create_session(self, start_time: datetime) -> int:
        """Create a new session and return its ID"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO sessions (start_time)
            VALUES (?)
        """, (start_time,))
        self.conn.commit()
        return cursor.lastrowid
    
    def update_session(self, session_id: int, data: Dict):
        """Update session with end data"""
        fields = []
        values = []
        
        for key, value in data.items():
            fields.append(f"{key} = ?")
            values.append(value)
        
        values.append(session_id)
        
        cursor = self.conn.cursor()
        cursor.execute(f"""
            UPDATE sessions
            SET {', '.join(fields)}
            WHERE id = ?
        """, values)
        self.conn.commit()
    
    def get_recent_sessions(self, limit: int = 10) -> List[Dict]:
        """Get recent sessions"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM sessions
            ORDER BY start_time DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]
    
    # ========================================================================
    # APP PATTERN TRACKING
    # ========================================================================
    
    def log_app_usage(self, app_name: str, duration_seconds: int, 
                      is_productive: bool = False, broke_flow: bool = False):
        """Log app usage and update patterns"""
        cursor = self.conn.cursor()
        
        # Get or create app pattern
        cursor.execute("""
            INSERT INTO app_patterns (app_name, total_time_seconds, last_used)
            VALUES (?, ?, ?)
            ON CONFLICT(app_name) DO UPDATE SET
                total_time_seconds = total_time_seconds + ?,
                flow_breaks = flow_breaks + ?,
                productive_sessions = productive_sessions + ?,
                distraction_sessions = distraction_sessions + ?,
                last_used = ?,
                updated_at = CURRENT_TIMESTAMP
        """, (
            app_name, duration_seconds, datetime.now(),
            duration_seconds,
            1 if broke_flow else 0,
            1 if is_productive else 0,
            1 if not is_productive else 0,
            datetime.now()
        ))
        self.conn.commit()
    
    def get_app_patterns(self, limit: int = 20) -> List[Dict]:
        """Get app usage patterns sorted by total time"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM app_patterns
            ORDER BY total_time_seconds DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_frequent_distractions(self, threshold: int = 5) -> List[str]:
        """Get apps that frequently break flow"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT app_name FROM app_patterns
            WHERE flow_breaks >= ?
            AND auto_blocked = 0
            ORDER BY flow_breaks DESC
        """, (threshold,))
        return [row['app_name'] for row in cursor.fetchall()]
    
    def auto_block_app(self, app_name: str):
        """Mark app as auto-blocked due to repeated flow breaks"""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE app_patterns
            SET auto_blocked = 1, is_blocked = 1, updated_at = CURRENT_TIMESTAMP
            WHERE app_name = ?
        """, (app_name,))
        self.conn.commit()
        logger.info(f"Auto-blocked app: {app_name}")
    
    # ========================================================================
    # BIOLOGICAL PATTERN ANALYSIS
    # ========================================================================
    
    def log_flow_window(self, date: datetime, hour: int, 
                        flow_quality: float, apm: float, duration_minutes: int):
        """Log flow quality for a specific time window"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO flow_windows (date, hour, flow_quality, apm_average, duration_minutes)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(date, hour) DO UPDATE SET
                flow_quality = (flow_quality + ?) / 2,
                apm_average = (apm_average + ?) / 2,
                duration_minutes = duration_minutes + ?
        """, (
            date.date(), hour, flow_quality, apm, duration_minutes,
            flow_quality, apm, duration_minutes
        ))
        self.conn.commit()
    
    def get_peak_flow_hours(self, days: int = 30) -> List[int]:
        """Get hours of day with highest flow quality"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT hour, AVG(flow_quality) as avg_quality
            FROM flow_windows
            WHERE date >= date('now', '-' || ? || ' days')
            GROUP BY hour
            HAVING COUNT(*) >= 3
            ORDER BY avg_quality DESC
            LIMIT 5
        """, (days,))
        return [row['hour'] for row in cursor.fetchall()]
    
    # ========================================================================
    # ACTIVITY LOGGING
    # ========================================================================
    
    def log_activity(self, session_id: int, app_name: str, 
                     activity_type: str, apm: float, fatigue_score: float,
                     url: Optional[str] = None):
        """Log detailed activity"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO activity_log 
            (session_id, timestamp, app_name, url, activity_type, apm, fatigue_score)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (session_id, datetime.now(), app_name, url, activity_type, apm, fatigue_score))
        self.conn.commit()
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

# Singleton instance
_db_instance = None

def get_db() -> LocalDatabase:
    """Get or create database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = LocalDatabase()
    return _db_instance

# Test
if __name__ == "__main__":
    db = LocalDatabase(Path("test_flow_patterns.db"))
    
    # Test session
    session_id = db.create_session(datetime.now())
    print(f"Created session: {session_id}")
    
    # Test app logging
    db.log_app_usage("vscode.exe", 300, is_productive=True)
    db.log_app_usage("chrome.exe", 120, broke_flow=True)
    
    # Test patterns
    patterns = db.get_app_patterns()
    print(f"App patterns: {patterns}")
    
    # Test flow windows
    db.log_flow_window(datetime.now(), 14, 85.0, 120.0, 25)
    peak_hours = db.get_peak_flow_hours()
    print(f"Peak flow hours: {peak_hours}")
    
    db.close()
    print("Database test complete!")

"""
Flow Engine - Pattern Analyzer
Analyzes historical data to learn user patterns and adapt system behavior.
Implements AI-driven learning without cloud dependencies.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from local_db import get_db

logger = logging.getLogger("FlowEngine.PatternAnalyzer")

class PatternAnalyzer:
    """
    Analyzes user patterns to enable adaptive learning.
    
    Features:
    - Identify apps that repeatedly break flow
    - Detect biological flow windows (time-of-day patterns)
    - Calculate optimal flow threshold based on history
    - Auto-adjust blocking rules
    """
    
    def __init__(self):
        self.db = get_db()
    
    # ========================================================================
    # APP PATTERN ANALYSIS
    # ========================================================================
    
    def analyze_app_patterns(self) -> Dict:
        """
        Analyze app usage patterns and identify problematic apps.
        
        Returns:
            Dict with frequent_distractions, productive_apps, and recommendations
        """
        patterns = self.db.get_app_patterns(limit=50)
        
        # Identify frequent distractions (flow_breaks >= 5)
        frequent_distractions = [
            p for p in patterns 
            if p['flow_breaks'] >= 5 and not p['auto_blocked']
        ]
        
        # Identify productive apps (high productive_sessions, low flow_breaks)
        productive_apps = [
            p for p in patterns
            if p['productive_sessions'] > p['distraction_sessions'] * 2
        ]
        
        # Generate recommendations
        recommendations = []
        for app in frequent_distractions:
            recommendations.append({
                'app_name': app['app_name'],
                'action': 'auto_block',
                'reason': f"Broke flow {app['flow_breaks']} times",
                'confidence': min(100, app['flow_breaks'] * 10)
            })
        
        return {
            'frequent_distractions': frequent_distractions,
            'productive_apps': productive_apps,
            'recommendations': recommendations
        }
    
    def apply_auto_blocking(self, threshold: int = 5) -> List[str]:
        """
        Auto-block apps that frequently break flow.
        
        Args:
            threshold: Number of flow breaks before auto-blocking
            
        Returns:
            List of newly blocked app names
        """
        distractions = self.db.get_frequent_distractions(threshold)
        
        blocked_apps = []
        for app_name in distractions:
            self.db.auto_block_app(app_name)
            blocked_apps.append(app_name)
            logger.info(f"🚫 Auto-blocked: {app_name}")
        
        return blocked_apps
    
    # ========================================================================
    # BIOLOGICAL PATTERN DETECTION
    # ========================================================================
    
    def detect_biological_patterns(self, days: int = 30) -> Dict:
        """
        Analyze time-of-day patterns to identify biological flow windows.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dict with peak_hours, low_hours, and schedule_recommendations
        """
        peak_hours = self.db.get_peak_flow_hours(days)
        
        # Get all flow windows for analysis
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT hour, AVG(flow_quality) as avg_quality, COUNT(*) as sessions
            FROM flow_windows
            WHERE date >= date('now', '-' || ? || ' days')
            GROUP BY hour
            HAVING COUNT(*) >= 2
            ORDER BY hour
        """, (days,))
        
        hourly_data = [dict(row) for row in cursor.fetchall()]
        
        # Identify low-quality hours
        low_hours = [
            h['hour'] for h in hourly_data
            if h['avg_quality'] < 50 and h['sessions'] >= 3
        ]
        
        # Generate schedule recommendations
        recommendations = []
        if peak_hours:
            recommendations.append({
                'type': 'schedule_deep_work',
                'hours': peak_hours,
                'reason': 'Historically high flow quality during these hours'
            })
        
        if low_hours:
            recommendations.append({
                'type': 'schedule_breaks',
                'hours': low_hours,
                'reason': 'Historically low flow quality - consider breaks'
            })
        
        return {
            'peak_hours': peak_hours,
            'low_hours': low_hours,
            'hourly_data': hourly_data,
            'recommendations': recommendations
        }
    
    # ========================================================================
    # DYNAMIC THRESHOLD CALCULATION
    # ========================================================================
    
    def calculate_optimal_threshold(self, baseline_minutes: int = 25) -> int:
        """
        Calculate optimal flow timer threshold based on user's historical performance.
        
        Implements progressive overload: if user consistently succeeds,
        increase the threshold by 10%.
        
        Args:
            baseline_minutes: Starting baseline (default: 25)
            
        Returns:
            Recommended threshold in minutes
        """
        # Get recent sessions (last 2 weeks)
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT duration_seconds, focus_score, resilience_score
            FROM sessions
            WHERE start_time >= datetime('now', '-14 days')
            AND duration_seconds > 0
            ORDER BY start_time DESC
            LIMIT 20
        """)
        
        sessions = [dict(row) for row in cursor.fetchall()]
        
        if len(sessions) < 5:
            # Not enough data, use baseline
            return baseline_minutes
        
        # Calculate success rate (sessions with focus_score > 70)
        successful_sessions = [
            s for s in sessions
            if s['focus_score'] and s['focus_score'] > 70
        ]
        
        success_rate = len(successful_sessions) / len(sessions)
        
        # Calculate average duration of successful sessions
        if successful_sessions:
            avg_duration = sum(s['duration_seconds'] for s in successful_sessions) / len(successful_sessions)
            avg_minutes = int(avg_duration / 60)
        else:
            avg_minutes = baseline_minutes
        
        # Progressive overload logic
        if success_rate > 0.8:
            # User is crushing it - increase threshold by 10%
            new_threshold = int(avg_minutes * 1.1)
            logger.info(f"📈 Progressive overload: {avg_minutes}min → {new_threshold}min (success rate: {success_rate*100:.0f}%)")
            return new_threshold
        elif success_rate < 0.4:
            # User is struggling - decrease threshold by 10%
            new_threshold = int(avg_minutes * 0.9)
            logger.info(f"📉 Adaptive reduction: {avg_minutes}min → {new_threshold}min (success rate: {success_rate*100:.0f}%)")
            return max(10, new_threshold)  # Minimum 10 minutes
        else:
            # Maintain current level
            return avg_minutes
    
    # ========================================================================
    # SESSION ANALYSIS
    # ========================================================================
    
    def analyze_session(self, session_data: Dict) -> Dict:
        """
        Analyze a completed session and extract insights.
        
        Args:
            session_data: Session data including duration, apps used, etc.
            
        Returns:
            Analysis results with insights and recommendations
        """
        insights = []
        
        # Analyze duration
        duration_minutes = session_data.get('duration_seconds', 0) / 60
        if duration_minutes > 60:
            insights.append({
                'type': 'achievement',
                'message': f'Deep work session: {duration_minutes:.0f} minutes!'
            })
        
        # Analyze focus score
        focus_score = session_data.get('focus_score', 0)
        if focus_score > 80:
            insights.append({
                'type': 'success',
                'message': 'High focus maintained throughout session'
            })
        elif focus_score < 50:
            insights.append({
                'type': 'warning',
                'message': 'Focus was fragmented - consider shorter sessions'
            })
        
        # Analyze distractions
        distraction_count = session_data.get('distraction_count', 0)
        if distraction_count > 5:
            insights.append({
                'type': 'recommendation',
                'message': 'High distraction count - review blocked apps list'
            })
        
        return {
            'insights': insights,
            'quality_score': (focus_score + (100 - distraction_count * 5)) / 2
        }
    
    # ========================================================================
    # LEARNING SUMMARY
    # ========================================================================
    
    def get_learning_summary(self) -> Dict:
        """
        Get a summary of what the system has learned about the user.
        
        Returns:
            Dict with learned patterns, stats, and recommendations
        """
        app_analysis = self.analyze_app_patterns()
        bio_patterns = self.detect_biological_patterns()
        optimal_threshold = self.calculate_optimal_threshold()
        
        # Get session stats
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT 
                COUNT(*) as total_sessions,
                SUM(duration_seconds) as total_time,
                AVG(focus_score) as avg_focus,
                SUM(distraction_count) as total_distractions
            FROM sessions
            WHERE start_time >= datetime('now', '-30 days')
        """)
        
        stats = dict(cursor.fetchone())
        
        return {
            'stats': {
                'total_sessions': stats['total_sessions'] or 0,
                'total_hours': (stats['total_time'] or 0) / 3600,
                'avg_focus_score': stats['avg_focus'] or 0,
                'total_distractions': stats['total_distractions'] or 0
            },
            'learned_patterns': {
                'peak_flow_hours': bio_patterns['peak_hours'],
                'problematic_apps': [a['app_name'] for a in app_analysis['frequent_distractions']],
                'optimal_threshold_minutes': optimal_threshold
            },
            'recommendations': (
                app_analysis['recommendations'] + 
                bio_patterns['recommendations']
            )
        }

# Singleton instance
_analyzer_instance = None

def get_analyzer() -> PatternAnalyzer:
    """Get or create analyzer instance"""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = PatternAnalyzer()
    return _analyzer_instance

# Test
if __name__ == "__main__":
    from local_db import LocalDatabase
    from pathlib import Path
    
    # Create test database
    db = LocalDatabase(Path("test_flow_patterns.db"))
    
    # Add test data
    session_id = db.create_session(datetime.now() - timedelta(hours=1))
    db.update_session(session_id, {
        'end_time': datetime.now(),
        'duration_seconds': 3600,
        'focus_score': 85.0,
        'distraction_count': 2
    })
    
    # Log some app usage
    db.log_app_usage("vscode.exe", 1800, is_productive=True)
    db.log_app_usage("chrome.exe", 600, broke_flow=True)
    db.log_app_usage("instagram.exe", 300, broke_flow=True)
    db.log_app_usage("instagram.exe", 300, broke_flow=True)
    db.log_app_usage("instagram.exe", 300, broke_flow=True)
    db.log_app_usage("instagram.exe", 300, broke_flow=True)
    db.log_app_usage("instagram.exe", 300, broke_flow=True)
    
    # Log flow window
    db.log_flow_window(datetime.now(), 14, 85.0, 120.0, 60)
    
    # Test analyzer
    analyzer = PatternAnalyzer()
    
    print("=== App Pattern Analysis ===")
    app_patterns = analyzer.analyze_app_patterns()
    print(f"Frequent distractions: {[a['app_name'] for a in app_patterns['frequent_distractions']]}")
    print(f"Recommendations: {app_patterns['recommendations']}")
    
    print("\n=== Biological Patterns ===")
    bio_patterns = analyzer.detect_biological_patterns()
    print(f"Peak hours: {bio_patterns['peak_hours']}")
    
    print("\n=== Optimal Threshold ===")
    threshold = analyzer.calculate_optimal_threshold()
    print(f"Recommended threshold: {threshold} minutes")
    
    print("\n=== Learning Summary ===")
    summary = analyzer.get_learning_summary()
    print(f"Total sessions: {summary['stats']['total_sessions']}")
    print(f"Learned patterns: {summary['learned_patterns']}")
    
    db.close()
    print("\nPattern analyzer test complete!")

"""
Flow Engine - Supabase Database Layer
Handles all database operations with Supabase for users, sessions, and stats.
"""

import os
from datetime import datetime, date
from typing import Optional, List, Dict
from dotenv import load_dotenv
from supabase import create_client, Client
from pydantic import BaseModel
import asyncio

load_dotenv()

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Initialize Supabase client
supabase: Client = None

def init_supabase():
    """Initialize Supabase client"""
    global supabase
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("⚠️  WARNING: Supabase credentials not configured. Using offline mode.")
        return None
    
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase connected successfully")
        return supabase
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        return None

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class User(BaseModel):
    id: Optional[int] = None
    name: str
    level: int = 1
    total_xp: int = 0
    baseline_focus_minutes: int = 25
    created_at: Optional[datetime] = None

class Session(BaseModel):
    id: Optional[int] = None
    user_id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: int = 0
    distraction_count: int = 0
    resilience_score: int = 0
    apm_average: float = 0.0
    flow_score: float = 0.0
    xp_earned: int = 0

class DailyStats(BaseModel):
    date: date
    user_id: int
    stamina_level: int = 0
    resilience_level: int = 0
    consistency_streak: int = 0
    total_xp_earned: int = 0
    sessions_completed: int = 0

# ============================================================================
# USER OPERATIONS
# ============================================================================

async def get_or_create_user(name: str = "Default User") -> Optional[User]:
    """Get existing user or create new one"""
    if not supabase:
        return User(id=1, name=name)  # Offline mode
    
    try:
        # Try to get existing user
        response = supabase.table('users').select('*').eq('name', name).execute()
        
        if response.data and len(response.data) > 0:
            return User(**response.data[0])
        
        # Create new user
        new_user = User(name=name, created_at=datetime.now())
        response = supabase.table('users').insert(new_user.dict(exclude={'id'})).execute()
        
        if response.data and len(response.data) > 0:
            return User(**response.data[0])
        
        return None
        
    except Exception as e:
        print(f"❌ Error getting/creating user: {e}")
        return User(id=1, name=name)  # Fallback

async def update_user_xp(user_id: int, xp_to_add: int) -> bool:
    """Add XP to user and update level if needed"""
    if not supabase:
        return True  # Offline mode
    
    try:
        # Get current user
        response = supabase.table('users').select('*').eq('id', user_id).execute()
        if not response.data:
            return False
        
        user = User(**response.data[0])
        user.total_xp += xp_to_add
        
        # Calculate new level (100 XP per level)
        new_level = (user.total_xp // 100) + 1
        if new_level > user.level:
            user.level = new_level
            print(f"🎉 LEVEL UP! Now Level {new_level}")
        
        # Update in database
        supabase.table('users').update({
            'total_xp': user.total_xp,
            'level': user.level
        }).eq('id', user_id).execute()
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating user XP: {e}")
        return False

async def update_baseline(user_id: int, new_baseline: int) -> bool:
    """Update user's baseline focus duration"""
    if not supabase:
        return True
    
    try:
        supabase.table('users').update({
            'baseline_focus_minutes': new_baseline
        }).eq('id', user_id).execute()
        return True
    except Exception as e:
        print(f"❌ Error updating baseline: {e}")
        return False

# ============================================================================
# SESSION OPERATIONS
# ============================================================================

async def create_session(session: Session) -> Optional[int]:
    """Create a new flow session"""
    if not supabase:
        return 1  # Offline mode
    
    try:
        response = supabase.table('sessions').insert(
            session.dict(exclude={'id'})
        ).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]['id']
        return None
        
    except Exception as e:
        print(f"❌ Error creating session: {e}")
        return None

async def update_session(session_id: int, updates: Dict) -> bool:
    """Update an existing session"""
    if not supabase:
        return True
    
    try:
        supabase.table('sessions').update(updates).eq('id', session_id).execute()
        return True
    except Exception as e:
        print(f"❌ Error updating session: {e}")
        return False

async def get_recent_sessions(user_id: int, limit: int = 10) -> List[Session]:
    """Get recent sessions for a user"""
    if not supabase:
        return []
    
    try:
        response = supabase.table('sessions').select('*').eq(
            'user_id', user_id
        ).order('start_time', desc=True).limit(limit).execute()
        
        return [Session(**s) for s in response.data]
        
    except Exception as e:
        print(f"❌ Error getting sessions: {e}")
        return []

async def get_user_average_session(user_id: int) -> float:
    """Calculate user's average session duration in minutes"""
    if not supabase:
        return 25.0
    
    try:
        response = supabase.table('sessions').select('duration_seconds').eq(
            'user_id', user_id
        ).not_.is_('end_time', 'null').execute()
        
        if not response.data:
            return 25.0
        
        durations = [s['duration_seconds'] for s in response.data]
        avg_seconds = sum(durations) / len(durations)
        return avg_seconds / 60.0  # Convert to minutes
        
    except Exception as e:
        print(f"❌ Error calculating average: {e}")
        return 25.0

# ============================================================================
# DAILY STATS OPERATIONS
# ============================================================================

async def get_or_create_daily_stats(user_id: int, target_date: date = None) -> DailyStats:
    """Get or create daily stats for a specific date"""
    if target_date is None:
        target_date = date.today()
    
    if not supabase:
        return DailyStats(date=target_date, user_id=user_id)
    
    try:
        # Try to get existing stats
        response = supabase.table('daily_stats').select('*').eq(
            'user_id', user_id
        ).eq('date', target_date.isoformat()).execute()
        
        if response.data and len(response.data) > 0:
            return DailyStats(**response.data[0])
        
        # Create new stats
        new_stats = DailyStats(date=target_date, user_id=user_id)
        response = supabase.table('daily_stats').insert(
            new_stats.dict()
        ).execute()
        
        if response.data and len(response.data) > 0:
            return DailyStats(**response.data[0])
        
        return new_stats
        
    except Exception as e:
        print(f"❌ Error getting daily stats: {e}")
        return DailyStats(date=target_date, user_id=user_id)

async def update_daily_stats(user_id: int, updates: Dict, target_date: date = None) -> bool:
    """Update daily stats"""
    if target_date is None:
        target_date = date.today()
    
    if not supabase:
        return True
    
    try:
        supabase.table('daily_stats').update(updates).eq(
            'user_id', user_id
        ).eq('date', target_date.isoformat()).execute()
        return True
    except Exception as e:
        print(f"❌ Error updating daily stats: {e}")
        return False

async def get_consistency_streak(user_id: int) -> int:
    """Calculate current consistency streak"""
    if not supabase:
        return 0
    
    try:
        # Get last 30 days of stats
        response = supabase.table('daily_stats').select('date, sessions_completed').eq(
            'user_id', user_id
        ).order('date', desc=True).limit(30).execute()
        
        if not response.data:
            return 0
        
        # Count consecutive days with sessions
        streak = 0
        current_date = date.today()
        
        for stat in response.data:
            stat_date = datetime.fromisoformat(stat['date']).date()
            
            if stat_date == current_date and stat['sessions_completed'] > 0:
                streak += 1
                current_date = current_date.replace(day=current_date.day - 1)
            else:
                break
        
        return streak
        
    except Exception as e:
        print(f"❌ Error calculating streak: {e}")
        return 0

# ============================================================================
# INITIALIZATION
# ============================================================================

# Initialize on module import
supabase = init_supabase()

# Test connection
if __name__ == "__main__":
    import asyncio
    
    async def test():
        print("Testing Supabase connection...")
        user = await get_or_create_user("Test User")
        print(f"User: {user}")
        
        if user and user.id:
            stats = await get_or_create_daily_stats(user.id)
            print(f"Daily Stats: {stats}")
            
            avg = await get_user_average_session(user.id)
            print(f"Average Session: {avg} minutes")
    
    asyncio.run(test())

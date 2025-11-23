"""
Flow Engine - Supabase Database Layer
Handles all database operations with Supabase for users, sessions, and stats.
"""

import os
import bcrypt
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
        print("WARNING: Supabase credentials not configured. Using offline mode.")
        return None
    
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("[OK] Supabase connected successfully")
        return supabase
    except Exception as e:
        print(f"[ERROR] Failed to connect to Supabase: {e}")
        return None

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class User(BaseModel):
    id: Optional[int] = None
    name: str
    username: Optional[str] = None
    password_hash: Optional[str] = None
    level: int = 1
    total_xp: int = 0
    baseline_focus_minutes: int = 25
    created_at: Optional[str] = None  # ISO format string
    cognitive_profile: Optional[Dict] = None  # JSON field: {focus, stamina, resilience, consistency}
    onboarding_data: Optional[Dict] = None  # JSON field: {timetable, work_type, challenges, goals}
    mission_log: Optional[Dict] = None  # JSON field: {goals, focus_areas}
    sessions_count: int = 0
    onboarding_complete: bool = False
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

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
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

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

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against a hash"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception:
        return False

async def create_user_with_auth(username: str, password: str, name: str) -> Optional[User]:
    """Create a new user with username and password"""
    if not supabase:
        print("[ERROR] Supabase not initialized")
        return None
    
    try:
        # Check if username already exists
        response = supabase.table('users').select('id').eq('username', username).execute()
        if response.data and len(response.data) > 0:
            print(f"[ERROR] Username '{username}' already exists")
            return None  # Username already exists
        
        # Hash password
        password_hash = hash_password(password)
        
        # Create new user
        new_user = User(
            name=name,
            username=username,
            password_hash=password_hash,
            created_at=datetime.now().isoformat(),  # Convert to ISO string
            cognitive_profile={"focus": 0, "stamina": 0, "resilience": 0, "consistency": 0},
            onboarding_data=None,
            mission_log=None,
            sessions_count=0,
            onboarding_complete=False
        )
        
        user_dict = new_user.dict(exclude={'id'})
        print(f"[DEBUG] Creating user with data: {list(user_dict.keys())}")
        
        response = supabase.table('users').insert(user_dict).execute()
        
        if response.data and len(response.data) > 0:
            user_data = response.data[0].copy()
            user_data.pop('password_hash', None)  # Don't return password hash
            return User(**user_data)
        
        print("[ERROR] No data returned from insert")
        return None
        
    except Exception as e:
        error_msg = str(e)
        print(f"[ERROR] Error creating user: {error_msg}")
        # Check if it's a column error
        if "column" in error_msg.lower() or "does not exist" in error_msg.lower():
            print("[ERROR] Database schema may be missing columns. Please run supabase_complete_schema.sql in Supabase SQL Editor.")
        raise  # Re-raise to get better error in API

async def authenticate_user(username: str, password: str) -> Optional[User]:
    """Authenticate a user by username and password"""
    if not supabase:
        return None
    
    try:
        response = supabase.table('users').select('*').eq('username', username).execute()
        
        if not response.data or len(response.data) == 0:
            return None
        
        user_data = response.data[0]
        stored_hash = user_data.get('password_hash')
        
        if not stored_hash or not verify_password(password, stored_hash):
            return None
        
        # Return user without password hash
        user_data.pop('password_hash', None)
        return User(**user_data)
        
    except Exception as e:
        print(f"[ERROR] Error authenticating user: {e}")
        return None

async def get_user_by_id(user_id: int) -> Optional[User]:
    """Get user by ID"""
    if not supabase:
        return None
    
    try:
        response = supabase.table('users').select('*').eq('id', user_id).execute()
        
        if response.data and len(response.data) > 0:
            user_data = response.data[0].copy()
            user_data.pop('password_hash', None)  # Don't return password hash
            return User(**user_data)
        
        return None
        
    except Exception as e:
        print(f"[ERROR] Error getting user by ID: {e}")
        return None

async def get_or_create_user(name: str = "Default User") -> Optional[User]:
    """Get existing user or create new one (legacy function for backward compatibility)"""
    if not supabase:
        return User(id=1, name=name)  # Offline mode
    
    try:
        # Try to get existing user
        response = supabase.table('users').select('*').eq('name', name).execute()
        
        if response.data and len(response.data) > 0:
            user_data = response.data[0].copy()
            user_data.pop('password_hash', None)
            return User(**user_data)
        
        # Create new user with default cognitive profile
        new_user = User(
            name=name,
            created_at=datetime.now().isoformat(),  # Convert to ISO string
            cognitive_profile={"focus": 0, "stamina": 0, "resilience": 0, "consistency": 0},
            onboarding_data=None,
            mission_log=None,
            sessions_count=0,
            onboarding_complete=False
        )
        response = supabase.table('users').insert(new_user.dict(exclude={'id'})).execute()
        
        if response.data and len(response.data) > 0:
            user_data = response.data[0].copy()
            user_data.pop('password_hash', None)
            return User(**user_data)
        
        return None
        
    except Exception as e:
        print(f"[ERROR] Error getting/creating user: {e}")
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
        print(f"[ERROR] Error updating user XP: {e}")
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
        print(f"[ERROR] Error updating baseline: {e}")
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
        print(f"[ERROR] Error creating session: {e}")
        return None

async def update_session(session_id: int, updates: Dict) -> bool:
    """Update an existing session"""
    if not supabase:
        return True
    
    try:
        supabase.table('sessions').update(updates).eq('id', session_id).execute()
        return True
    except Exception as e:
        print(f"[ERROR] Error updating session: {e}")
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
        print(f"[ERROR] Error getting sessions: {e}")
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
        print(f"[ERROR] Error calculating average: {e}")
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
        print(f"[ERROR] Error getting daily stats: {e}")
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
        print(f"[ERROR] Error updating daily stats: {e}")
        return False

async def get_user_status(user_id: int) -> Dict:
    """Get user status for onboarding check"""
    if not supabase:
        return {
            "is_new": True,
            "onboarding_complete": False,
            "sessions_count": 0
        }
    
    try:
        response = supabase.table('users').select('sessions_count, onboarding_complete, created_at').eq('id', user_id).execute()
        if not response.data:
            return {
                "is_new": True,
                "onboarding_complete": False,
                "sessions_count": 0
            }
        
        user_data = response.data[0]
        sessions_count = user_data.get('sessions_count', 0)
        onboarding_complete = user_data.get('onboarding_complete', False)
        
        # User is new if they have 0 sessions
        is_new = sessions_count == 0
        
        return {
            "is_new": is_new,
            "onboarding_complete": onboarding_complete,
            "sessions_count": sessions_count
        }
    except Exception as e:
        print(f"[ERROR] Error getting user status: {e}")
        return {
            "is_new": True,
            "onboarding_complete": False,
            "sessions_count": 0
        }

async def update_mission_log(user_id: int, mission_log: Dict) -> bool:
    """Update user mission log"""
    if not supabase:
        return True
    
    try:
        supabase.table('users').update({
            'mission_log': mission_log
        }).eq('id', user_id).execute()
        return True
    except Exception as e:
        print(f"[ERROR] Error updating mission log: {e}")
        return False

async def update_onboarding_data(user_id: int, onboarding_data: Dict) -> bool:
    """Update user onboarding data"""
    if not supabase:
        return True
    
    try:
        supabase.table('users').update({
            'onboarding_data': onboarding_data,
            'onboarding_complete': True
        }).eq('id', user_id).execute()
        return True
    except Exception as e:
        print(f"[ERROR] Error updating onboarding data: {e}")
        return False

async def increment_sessions_count(user_id: int) -> bool:
    """Increment user's session count"""
    if not supabase:
        return True
    
    try:
        # Get current count
        response = supabase.table('users').select('sessions_count').eq('id', user_id).execute()
        if not response.data:
            return False
        
        current_count = response.data[0].get('sessions_count', 0)
        supabase.table('users').update({
            'sessions_count': current_count + 1
        }).eq('id', user_id).execute()
        return True
    except Exception as e:
        print(f"[ERROR] Error incrementing sessions count: {e}")
        return False

async def update_cognitive_profile(user_id: int, profile: Dict) -> bool:
    """Update user's cognitive profile"""
    if not supabase:
        return True
    
    try:
        supabase.table('users').update({
            'cognitive_profile': profile
        }).eq('id', user_id).execute()
        return True
    except Exception as e:
        print(f"[ERROR] Error updating cognitive profile: {e}")
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
        print(f"[ERROR] Error calculating streak: {e}")
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

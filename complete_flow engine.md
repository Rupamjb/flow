# Flow Engine Behavior & Onboarding Redesign Plan

## Overview

Major redesign of intervention system and onboarding flow: remove cooldown timers, implement gradual resilience decay, add AI-powered onboarding with cognitive profile tracking, and create web-based onboarding integrated with dashboard.

## Key Changes

### 1. Intervention System Redesign

**Remove Cooldown Timers:**

- Remove cooldown functionality from `blocker.py`
- "OPEN ANYWAY" allows immediate access to apps/tabs
- No blocking or waiting period

**Resilience Decay System:**

- Instant penalty: -10 resilience when user chooses "OPEN ANYWAY"
- Gradual decay: -1 resilience per minute spent in distracting app/tab during flow
- Track time spent in distracting content per session
- Update resilience in real-time during flow sessions

**"WAIT FOR BREAK" Behavior:**

- Close app/tab immediately (for browser: close tab, for apps: minimize/close window)
- Increase resilience: +5 resilience
- Grant XP bonus: +10 XP (XP_RESUME_BONUS)
- Log positive action to database

### 2. Web-Based Onboarding System

**Dashboard Integration:**

- Frontend checks user status on load: `/api/user/status` endpoint
- Returns: `{"is_new": true/false, "onboarding_complete": true/false, "sessions_count": N}`
- If new user: redirect to onboarding flow
- If existing but incomplete: show onboarding completion prompt

**Onboarding Questions:**

1. Daily timetable (start/end times for work)
2. Primary work type (coding, writing, design, research, etc.)
3. Current productivity challenges
4. Goals/objectives

**AI Analysis (Groq API):**

- Send responses to Groq API for analysis
- Generate:
- Personalized schedule with predicted flow windows
- Initial mission log with goals
- Recommended baseline focus duration
- Productive/distracting app suggestions

**Backend Endpoints:**

- `POST /api/onboarding/submit` - Submit onboarding responses
- `POST /api/onboarding/analyze` - AI analysis of responses
- `GET /api/user/status` - Check if user is new/existing

### 3. Cognitive Profile System

**Initial State:**

- Cognitive profile starts at 0 (all stats at 0)
- Profile includes: Focus, Stamina, Resilience, Consistency
- Stored in database: `users.cognitive_profile` (JSON field)

**After 3 Sessions:**

- AI analyzes performance from first 3 sessions
- Calculates baseline cognitive profile:
- Average focus scores
- Average stamina (session duration)
- Average resilience (resistance to distractions)
- Consistency (session frequency)
- Sets minimum cognitive profile values
- Stores in database

**Progressive Building:**

- After 3 sessions, user gains XP and levels up
- Each level up increases cognitive profile stats
- Profile displayed in dashboard
- Used for personalized recommendations

**Database Schema Updates:**

- Add `cognitive_profile` JSON field to users table
- Add `onboarding_data` JSON field to users table
- Add `sessions_count` integer field to users table
- Add `onboarding_complete` boolean field to users table

### 4. Implementation Tasks

**Backend Changes:**

1. Remove cooldown timer from `blocker.py`
2. Update `handle_break()` to allow immediate access + instant resilience penalty
3. Add gradual resilience decay tracking in `main.py`
4. Update `handle_resume()` to close apps/tabs and grant rewards
5. Create onboarding API endpoints
6. Add AI analysis function using Groq API
7. Add cognitive profile calculation after 3 sessions
8. Update database schema and models
9. Add user status endpoint

**Frontend Changes:**

1. Create onboarding component/page
2. Add user status check on dashboard load
3. Implement onboarding form with questions
4. Add AI analysis loading state
5. Display cognitive profile in dashboard
6. Show onboarding completion status

**Chrome Extension Changes:**

1. Update to close tabs when "WAIT FOR BREAK" is chosen
2. Remove cooldown-related UI elements

## Files to Modify

1. `backend/main.py` - Remove cooldown, add resilience decay, onboarding endpoints
2. `backend/blocker.py` - Remove cooldown functionality, update to close apps/tabs
3. `backend/database.py` - Add cognitive profile fields, onboarding data storage
4. `backend/onboarding.py` - Convert to API-based, add AI analysis
5. `frontend-react/src/App.jsx` - Add onboarding check and flow
6. `frontend-react/src/components/Onboarding.jsx` - New component
7. `extension/background.js` - Update tab closing behavior
8. `SUPABASE_SCHEMA.md` - Update schema documentation

## Testing Checklist

- [ ] "OPEN ANYWAY" allows immediate access
- [ ] Instant resilience penalty applied
- [ ] Gradual resilience decay works during distracting app usage
- [ ] "WAIT FOR BREAK" closes apps/tabs immediately
- [ ] Resilience and XP increase on "WAIT FOR BREAK"
- [ ] Dashboard checks user status on load
- [ ] New users see onboarding flow
- [ ] Onboarding questions submitted correctly
- [ ] AI analysis generates personalized schedule
- [ ] Cognitive profile starts at 0
- [ ] Profile calculated after 3 sessions
- [ ] Profile increases with level ups
- [ ] All database fields updated correctly
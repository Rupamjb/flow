-- Complete Supabase Schema for Flow Engine
-- Run this in your Supabase SQL Editor to set up the complete database

-- Users table with all fields including onboarding, cognitive profile, and authentication
CREATE TABLE IF NOT EXISTS users (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  username TEXT UNIQUE,
  password_hash TEXT,
  level INTEGER DEFAULT 1,
  total_xp INTEGER DEFAULT 0,
  baseline_focus_minutes INTEGER DEFAULT 25,
  cognitive_profile JSONB DEFAULT '{"focus": 0, "stamina": 0, "resilience": 0, "consistency": 0}'::jsonb,
  onboarding_data JSONB,
  mission_log JSONB,
  sessions_count INTEGER DEFAULT 0,
  onboarding_complete BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
  start_time TIMESTAMP WITH TIME ZONE NOT NULL,
  end_time TIMESTAMP WITH TIME ZONE,
  duration_seconds INTEGER DEFAULT 0,
  distraction_count INTEGER DEFAULT 0,
  resilience_score INTEGER DEFAULT 0,
  apm_average REAL DEFAULT 0.0,
  flow_score REAL DEFAULT 0.0,
  xp_earned INTEGER DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Daily stats table
CREATE TABLE IF NOT EXISTS daily_stats (
  date DATE NOT NULL,
  user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
  stamina_level INTEGER DEFAULT 0,
  resilience_level INTEGER DEFAULT 0,
  consistency_streak INTEGER DEFAULT 0,
  total_xp_earned INTEGER DEFAULT 0,
  sessions_completed INTEGER DEFAULT 0,
  PRIMARY KEY (date, user_id)
);

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_start_time ON sessions(start_time DESC);
CREATE INDEX IF NOT EXISTS idx_daily_stats_user_id ON daily_stats(user_id);
CREATE INDEX IF NOT EXISTS idx_daily_stats_date ON daily_stats(date DESC);

-- Enable Row Level Security (RLS)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_stats ENABLE ROW LEVEL SECURITY;

-- Create policies (allow all for now - customize based on your auth setup)
DROP POLICY IF EXISTS "Allow all operations on users" ON users;
CREATE POLICY "Allow all operations on users" ON users FOR ALL USING (true);

DROP POLICY IF EXISTS "Allow all operations on sessions" ON sessions;
CREATE POLICY "Allow all operations on sessions" ON sessions FOR ALL USING (true);

DROP POLICY IF EXISTS "Allow all operations on daily_stats" ON daily_stats;
CREATE POLICY "Allow all operations on daily_stats" ON daily_stats FOR ALL USING (true);

-- If tables already exist, add missing columns
DO $$ 
BEGIN
  -- Add cognitive_profile if it doesn't exist
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'users' AND column_name = 'cognitive_profile'
  ) THEN
    ALTER TABLE users ADD COLUMN cognitive_profile JSONB DEFAULT '{"focus": 0, "stamina": 0, "resilience": 0, "consistency": 0}'::jsonb;
  END IF;

  -- Add onboarding_data if it doesn't exist
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'users' AND column_name = 'onboarding_data'
  ) THEN
    ALTER TABLE users ADD COLUMN onboarding_data JSONB;
  END IF;

  -- Add sessions_count if it doesn't exist
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'users' AND column_name = 'sessions_count'
  ) THEN
    ALTER TABLE users ADD COLUMN sessions_count INTEGER DEFAULT 0;
  END IF;

  -- Add onboarding_complete if it doesn't exist
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'users' AND column_name = 'onboarding_complete'
  ) THEN
    ALTER TABLE users ADD COLUMN onboarding_complete BOOLEAN DEFAULT FALSE;
  END IF;

  -- Add username if it doesn't exist
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'users' AND column_name = 'username'
  ) THEN
    ALTER TABLE users ADD COLUMN username TEXT UNIQUE;
  END IF;

  -- Add password_hash if it doesn't exist
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'users' AND column_name = 'password_hash'
  ) THEN
    ALTER TABLE users ADD COLUMN password_hash TEXT;
  END IF;

  -- Add mission_log if it doesn't exist
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'users' AND column_name = 'mission_log'
  ) THEN
    ALTER TABLE users ADD COLUMN mission_log JSONB;
  END IF;

  -- Update existing users with default values
  UPDATE users 
  SET cognitive_profile = COALESCE(cognitive_profile, '{"focus": 0, "stamina": 0, "resilience": 0, "consistency": 0}'::jsonb),
      sessions_count = COALESCE(sessions_count, 0),
      onboarding_complete = COALESCE(onboarding_complete, FALSE)
  WHERE cognitive_profile IS NULL OR sessions_count IS NULL OR onboarding_complete IS NULL;
END $$;

-- Verify the schema
SELECT 
  table_name,
  column_name,
  data_type,
  column_default
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name IN ('users', 'sessions', 'daily_stats')
ORDER BY table_name, ordinal_position;


# Supabase Schema Setup for Flow Engine

This document contains the SQL schema for setting up your Supabase database.

## Setup Instructions

1. Go to your Supabase project dashboard
2. Navigate to the SQL Editor
3. Create a new query
4. Copy and paste the schema below
5. Run the query

## Database Schema

```sql
-- Users table
CREATE TABLE IF NOT EXISTS users (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  level INTEGER DEFAULT 1,
  total_xp INTEGER DEFAULT 0,
  baseline_focus_minutes INTEGER DEFAULT 25,
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
CREATE POLICY "Allow all operations on users" ON users FOR ALL USING (true);
CREATE POLICY "Allow all operations on sessions" ON sessions FOR ALL USING (true);
CREATE POLICY "Allow all operations on daily_stats" ON daily_stats FOR ALL USING (true);
```

## Verification

After running the schema, verify the tables were created:

```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('users', 'sessions', 'daily_stats');
```

You should see all three tables listed.

## Test Data (Optional)

Insert a test user to verify everything works:

```sql
INSERT INTO users (name, level, total_xp, baseline_focus_minutes)
VALUES ('Test User', 1, 0, 25)
RETURNING *;
```

## Environment Configuration

After setting up the schema, update your `.env` file:

```
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-key-here
```

You can find these values in your Supabase project settings under "API".

## Next Steps

1. Run the schema SQL in Supabase
2. Update your `.env` file with credentials
3. Restart the Flow Engine backend
4. Check the console for "✅ Supabase connected successfully"

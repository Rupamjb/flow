# Supabase Setup Guide

## Step 1: Run the Database Schema

1. Go to your Supabase project: https://app.supabase.com
2. Navigate to **SQL Editor** (left sidebar)
3. Click **New Query**
4. Copy and paste the entire contents of `supabase_complete_schema.sql`
5. Click **Run** (or press F5)

This will create:
- `users` table with all fields (including cognitive_profile, onboarding_data, etc.)
- `sessions` table
- `daily_stats` table
- All necessary indexes and policies

## Step 2: Verify Schema

After running the schema, verify it worked:

```sql
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'users'
ORDER BY ordinal_position;
```

You should see these columns:
- id
- name
- level
- total_xp
- baseline_focus_minutes
- **cognitive_profile** (JSONB)
- **onboarding_data** (JSONB)
- **sessions_count** (INTEGER)
- **onboarding_complete** (BOOLEAN)
- created_at

## Step 3: Test Connection

Run the test script:
```bash
python test_supabase_setup.py
```

You should see:
- [OK] Connected to Supabase successfully
- [OK] User created/retrieved with all fields

## Step 4: Verify Environment Variables

Your `.env` file should have:
```
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-key-here
```

## Troubleshooting

**Error: "Could not find the table 'public.users' in the schema cache"**
- The table doesn't exist yet - run the SQL schema first
- Or refresh the Supabase schema cache (wait a few seconds)

**Error: "permission denied"**
- Check Row Level Security (RLS) policies in Supabase
- The schema includes policies that allow all operations

**Cognitive Profile is None**
- The column might not exist - run the schema update SQL
- Or the user was created before the schema update


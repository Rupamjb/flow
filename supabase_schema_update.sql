-- Updated Supabase Schema for Flow Engine
-- Run this in your Supabase SQL Editor to add new fields

-- Add new columns to users table for onboarding and cognitive profile
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS cognitive_profile JSONB DEFAULT '{"focus": 0, "stamina": 0, "resilience": 0, "consistency": 0}'::jsonb,
ADD COLUMN IF NOT EXISTS onboarding_data JSONB,
ADD COLUMN IF NOT EXISTS sessions_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS onboarding_complete BOOLEAN DEFAULT FALSE;

-- Update existing users to have default cognitive profile if null
UPDATE users 
SET cognitive_profile = '{"focus": 0, "stamina": 0, "resilience": 0, "consistency": 0}'::jsonb
WHERE cognitive_profile IS NULL;

-- Update existing users to have default sessions_count if null
UPDATE users 
SET sessions_count = 0
WHERE sessions_count IS NULL;

-- Update existing users to have default onboarding_complete if null
UPDATE users 
SET onboarding_complete = FALSE
WHERE onboarding_complete IS NULL;

-- Verify the changes
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'users'
AND column_name IN ('cognitive_profile', 'onboarding_data', 'sessions_count', 'onboarding_complete');


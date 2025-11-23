"""
Verify Supabase schema has all required fields
"""
import sys
import os
sys.path.insert(0, 'backend')

from dotenv import load_dotenv
load_dotenv()

from database import init_supabase

print("=" * 60)
print("Supabase Schema Verification")
print("=" * 60)

client = init_supabase()
if not client:
    print("[ERROR] Could not connect to Supabase")
    sys.exit(1)

print("\n[OK] Connected to Supabase")

# Check if users table exists and has required columns
print("\nChecking users table schema...")
try:
    # Try to query the table structure
    result = client.table('users').select('id, name, level, total_xp, baseline_focus_minutes, cognitive_profile, onboarding_data, sessions_count, onboarding_complete').limit(1).execute()
    print("[OK] Users table exists and is accessible")
    
    # Check if we can read the new fields
    if result.data:
        user_data = result.data[0]
        print("\nTable columns found:")
        for key in ['id', 'name', 'level', 'total_xp', 'baseline_focus_minutes', 'cognitive_profile', 'onboarding_data', 'sessions_count', 'onboarding_complete']:
            if key in user_data:
                print(f"  [OK] {key}: {type(user_data[key]).__name__}")
            else:
                print(f"  [MISSING] {key}")
    
    print("\n[SUCCESS] All required fields are present!")
    print("\nNext: Run the Flow Engine backend to start using Supabase")
    
except Exception as e:
    error_msg = str(e)
    if "Could not find the table" in error_msg or "PGRST205" in error_msg:
        print("\n[ERROR] Users table does not exist in Supabase")
        print("\nACTION REQUIRED:")
        print("1. Go to https://app.supabase.com")
        print("2. Open SQL Editor")
        print("3. Run the SQL from: supabase_complete_schema.sql")
        print("4. Then run this script again")
    elif "column" in error_msg.lower() or "does not exist" in error_msg.lower():
        print("\n[ERROR] Some columns are missing")
        print("\nACTION REQUIRED:")
        print("1. Go to https://app.supabase.com")
        print("2. Open SQL Editor")
        print("3. Run the SQL from: supabase_schema_update.sql")
        print("4. This will add the missing columns")
    else:
        print(f"\n[ERROR] {error_msg}")
        print("\nCheck your Supabase project settings and RLS policies")

print("\n" + "=" * 60)


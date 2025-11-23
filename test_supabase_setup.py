"""
Test Supabase connection and schema setup
"""
import sys
import os
sys.path.insert(0, 'backend')

from dotenv import load_dotenv
load_dotenv()

from database import init_supabase, get_or_create_user
import asyncio

print("=" * 60)
print("Supabase Setup Test")
print("=" * 60)

# Check environment variables
print("\n1. Checking Environment Variables:")
supabase_url = os.getenv("SUPABASE_URL", "")
supabase_key = os.getenv("SUPABASE_KEY", "")

if supabase_url and supabase_key:
    print(f"   [OK] SUPABASE_URL: {supabase_url[:30]}...")
    print(f"   [OK] SUPABASE_KEY: {supabase_key[:30]}...")
else:
    print("   [ERROR] Missing Supabase credentials in .env file")
    sys.exit(1)

# Test connection
print("\n2. Testing Supabase Connection:")
client = init_supabase()

if not client:
    print("   [ERROR] Failed to connect to Supabase")
    print("   [INFO] Check your SUPABASE_URL and SUPABASE_KEY in .env file")
    sys.exit(1)

print("   [OK] Connected to Supabase successfully")

# Test user creation/retrieval
print("\n3. Testing User Operations:")
async def test_user_ops():
    try:
        user = await get_or_create_user("Test User")
        if user:
            print(f"   [OK] User created/retrieved: {user.name} (ID: {user.id})")
            print(f"   [OK] Level: {user.level}, XP: {user.total_xp}")
            print(f"   [OK] Cognitive Profile: {user.cognitive_profile}")
            print(f"   [OK] Sessions Count: {user.sessions_count}")
            print(f"   [OK] Onboarding Complete: {user.onboarding_complete}")
            return True
        else:
            print("   [ERROR] Failed to create/retrieve user")
            return False
    except Exception as e:
        print(f"   [ERROR] User operation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

result = asyncio.run(test_user_ops())

print("\n" + "=" * 60)
if result:
    print("SUPABASE SETUP: SUCCESS")
    print("=" * 60)
    print("\nNext Steps:")
    print("1. Run the SQL schema update in Supabase SQL Editor:")
    print("   File: supabase_schema_update.sql")
    print("2. This will add the new fields (cognitive_profile, etc.)")
    print("3. Restart the Flow Engine backend")
else:
    print("SUPABASE SETUP: FAILED")
    print("=" * 60)
    print("\nTroubleshooting:")
    print("1. Check your .env file has correct SUPABASE_URL and SUPABASE_KEY")
    print("2. Verify your Supabase project is active")
    print("3. Check if the database schema is set up (see SUPABASE_SCHEMA.md)")
print("=" * 60)


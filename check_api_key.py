"""
Simple test to verify Groq API key is set
"""

import os

# Check for API key in environment
api_key = os.getenv('AI_API_KEY')

if api_key:
    print(f"✓ API Key found: {api_key[:10]}...{api_key[-4:]}")
    print(f"✓ Key length: {len(api_key)} characters")
else:
    print("❌ AI_API_KEY not found in environment variables")
    print("\nTo set it:")
    print("1. PowerShell: $env:AI_API_KEY='your_key_here'")
    print("2. Or create .env file with: AI_API_KEY=your_key_here")
    
# Try loading from .env
try:
    from dotenv import load_dotenv
    load_dotenv()
    api_key_from_env = os.getenv('AI_API_KEY')
    if api_key_from_env:
        print(f"\n✓ Also found in .env file")
except ImportError:
    print("\n⚠️  python-dotenv not installed")

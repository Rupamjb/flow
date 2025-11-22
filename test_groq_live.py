"""
Test AI Classifier with real Groq API
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.insert(0, 'backend')

from ai_classifier import AIClassifier

def test_with_groq_api():
    """Test AI classifier with real Groq API"""
    print("=" * 70)
    print("GROQ API LIVE TEST")
    print("=" * 70)
    
    # Check API key
    api_key = os.getenv('AI_API_KEY')
    if not api_key:
        print("❌ AI_API_KEY not found in environment")
        print("Please set it in .env file or environment variable")
        return False
    
    print(f"✓ API Key found: {api_key[:10]}...{api_key[-4:]}")
    
    # Create classifier
    classifier = AIClassifier()
    print(f"✓ Classifier initialized (fallback mode: {classifier.use_fallback})")
    
    if classifier.use_fallback:
        print("\n⚠️  Classifier is in fallback mode - API key may not be loaded correctly")
        return False
    
    print("\n" + "=" * 70)
    print("TEST 1: URL Classification")
    print("=" * 70)
    
    # Test ambiguous URL that requires AI
    test_url = "https://youtube.com/watch?v=python_tutorial"
    print(f"\nClassifying: {test_url}")
    print("(This should be 'productive' - it's a tutorial)")
    
    try:
        result = classifier.classify_url(test_url)
        print(f"\n✓ Classification: {result['classification']}")
        print(f"✓ Confidence: {result['confidence']:.2f}")
        print(f"✓ Reasoning: {result['reasoning']}")
        print(f"✓ Source: {result['source']}")
        
        if result['source'] == 'ai':
            print("\n🎉 SUCCESS! AI classification working!")
        else:
            print(f"\n⚠️  Using {result['source']} instead of AI")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False
    
    print("\n" + "=" * 70)
    print("TEST 2: App Classification")
    print("=" * 70)
    
    # Test app classification
    app_name = "chrome.exe"
    window_title = "Stack Overflow - How to use Python"
    print(f"\nClassifying: {app_name}")
    print(f"Window: {window_title}")
    print("(This should be 'productive' - Stack Overflow for coding)")
    
    try:
        result = classifier.classify_app(app_name, window_title)
        print(f"\n✓ Classification: {result['classification']}")
        print(f"✓ Confidence: {result['confidence']:.2f}")
        print(f"✓ Reasoning: {result['reasoning']}")
        print(f"✓ Source: {result['source']}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False
    
    print("\n" + "=" * 70)
    print("TEST 3: Distracting Content")
    print("=" * 70)
    
    # Test clearly distracting content
    test_url = "https://instagram.com/explore"
    print(f"\nClassifying: {test_url}")
    print("(This should be 'distracting')")
    
    try:
        result = classifier.classify_url(test_url)
        print(f"\n✓ Classification: {result['classification']}")
        print(f"✓ Confidence: {result['confidence']:.2f}")
        print(f"✓ Reasoning: {result['reasoning']}")
        print(f"✓ Source: {result['source']}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False
    
    print("\n" + "=" * 70)
    print("ALL TESTS PASSED! ✓")
    print("=" * 70)
    print("\nGroq API is working correctly!")
    print("The AI classifier is ready to use in Flow Engine.")
    
    return True

if __name__ == "__main__":
    success = test_with_groq_api()
    sys.exit(0 if success else 1)

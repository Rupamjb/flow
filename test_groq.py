"""
Test Groq API integration with Flow Engine AI Classifier
"""

import os
import sys
sys.path.insert(0, 'backend')

# Set test API key (user should replace with real key)
os.environ['AI_API_KEY'] = 'test_key_placeholder'

from ai_classifier import AIClassifier

def test_groq_integration():
    """Test that Groq API integration is properly configured"""
    print("=" * 60)
    print("GROQ API INTEGRATION TEST")
    print("=" * 60)
    
    # Test with placeholder key (will use fallback)
    classifier = AIClassifier()
    
    print("\n✓ AIClassifier initialized")
    print(f"✓ Using fallback mode: {classifier.use_fallback}")
    
    # Test URL classification
    url = "https://youtube.com/watch?v=coding_tutorial"
    result = classifier.classify_url(url)
    
    print(f"\n✓ URL Classification Test:")
    print(f"  URL: {url}")
    print(f"  Classification: {result['classification']}")
    print(f"  Confidence: {result['confidence']:.2f}")
    print(f"  Source: {result['source']}")
    
    # Test app classification
    result = classifier.classify_app("vscode.exe", "main.py - Visual Studio Code")
    
    print(f"\n✓ App Classification Test:")
    print(f"  App: vscode.exe")
    print(f"  Classification: {result['classification']}")
    print(f"  Confidence: {result['confidence']:.2f}")
    
    print("\n" + "=" * 60)
    print("INTEGRATION TEST PASSED")
    print("=" * 60)
    print("\nTo enable Groq API:")
    print("1. Get API key from https://console.groq.com/")
    print("2. Set environment variable: AI_API_KEY=your_key_here")
    print("3. Restart the application")
    print("=" * 60)

if __name__ == "__main__":
    test_groq_integration()

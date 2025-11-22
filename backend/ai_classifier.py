"""
Flow Engine - AI Classifier
Uses AI API to intelligently classify URLs and apps as productive or distracting.
Context-aware: considers time, task, and user patterns.
"""

import os
import logging
from typing import Dict, Optional, Literal
from datetime import datetime
import json

logger = logging.getLogger("FlowEngine.AIClassifier")

# AI API Configuration
AI_API_KEY = os.getenv("AI_API_KEY", "")  # User will provide
AI_API_ENDPOINT = os.getenv("AI_API_ENDPOINT", "")  # User will provide

class AIClassifier:
    """
    AI-powered classifier for URLs and applications.
    
    Uses AI API to determine if content is productive or distracting
    based on context, user patterns, and content analysis.
    """
    
    def __init__(self, api_key: Optional[str] = None, endpoint: Optional[str] = None):
        self.api_key = api_key or AI_API_KEY
        self.endpoint = endpoint or AI_API_ENDPOINT
        self.cache = {}  # Cache classifications to reduce API calls
        
        if not self.api_key:
            logger.warning("AI API key not configured. Using fallback keyword matching.")
            self.use_fallback = True
        else:
            self.use_fallback = False
            logger.info("AI classifier initialized with API")
    
    def classify_url(self, url: str, context: Optional[Dict] = None) -> Dict:
        """
        Classify a URL as productive or distracting.
        
        Args:
            url: The URL to classify
            context: Optional context (current_task, time_of_day, etc.)
            
        Returns:
            Dict with classification, confidence, and reasoning
        """
        # Check cache first
        cache_key = f"url:{url}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        if self.use_fallback:
            return self._fallback_url_classification(url)
        
        # Prepare AI prompt
        prompt = self._build_url_prompt(url, context)
        
        # Call AI API (placeholder - user will provide actual implementation)
        try:
            result = self._call_ai_api(prompt)
            classification = self._parse_ai_response(result)
            
            # Cache result
            self.cache[cache_key] = classification
            return classification
            
        except Exception as e:
            logger.error(f"AI classification failed: {e}. Using fallback.")
            return self._fallback_url_classification(url)
    
    def classify_app(self, app_name: str, window_title: str, context: Optional[Dict] = None) -> Dict:
        """
        Classify an application as productive or distracting.
        
        Args:
            app_name: The application executable name
            window_title: The current window title
            context: Optional context
            
        Returns:
            Dict with classification, confidence, and reasoning
        """
        # Check cache
        cache_key = f"app:{app_name}:{window_title[:50]}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        if self.use_fallback:
            return self._fallback_app_classification(app_name, window_title)
        
        # Prepare AI prompt
        prompt = self._build_app_prompt(app_name, window_title, context)
        
        # Call AI API
        try:
            result = self._call_ai_api(prompt)
            classification = self._parse_ai_response(result)
            
            # Cache result
            self.cache[cache_key] = classification
            return classification
            
        except Exception as e:
            logger.error(f"AI classification failed: {e}. Using fallback.")
            return self._fallback_app_classification(app_name, window_title)
    
    def _build_url_prompt(self, url: str, context: Optional[Dict]) -> str:
        """Build AI prompt for URL classification"""
        context_str = ""
        if context:
            context_str = f"\nContext: {json.dumps(context, indent=2)}"
        
        return f"""Classify this URL as either "productive" or "distracting" for a user in deep work mode.

URL: {url}{context_str}

Consider:
- Is this URL related to work, learning, or research? (productive)
- Is this URL related to entertainment, social media, or procrastination? (distracting)
- Context matters: YouTube can be productive (tutorials) or distracting (entertainment)

Respond in JSON format:
{{
    "classification": "productive" or "distracting",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation"
}}"""
    
    def _build_app_prompt(self, app_name: str, window_title: str, context: Optional[Dict]) -> str:
        """Build AI prompt for app classification"""
        context_str = ""
        if context:
            context_str = f"\nContext: {json.dumps(context, indent=2)}"
        
        return f"""Classify this application as either "productive" or "distracting" for a user in deep work mode.

Application: {app_name}
Window Title: {window_title}{context_str}

Consider:
- Is this app used for work, coding, writing, or learning? (productive)
- Is this app used for entertainment, gaming, or social media? (distracting)
- Window title provides context about current activity

Respond in JSON format:
{{
    "classification": "productive" or "distracting",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation"
}}"""
    
    def _call_ai_api(self, prompt: str) -> str:
        """
        Call Groq API with the prompt.
        Uses llama-3.1-8b-instant for fast, accurate classification.
        """
        import requests
        
        if not self.api_key:
            raise ValueError("Groq API key not configured")
        
        # Groq API endpoint
        url = "https://api.groq.com/openai/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a productivity assistant that classifies URLs and apps as productive or distracting. Always respond in valid JSON format."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 150
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            return result['choices'][0]['message']['content']
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Groq API request failed: {e}")
            raise
        except (KeyError, IndexError) as e:
            logger.error(f"Unexpected Groq API response format: {e}")
            raise
    
    def _parse_ai_response(self, response: str) -> Dict:
        """Parse AI API response"""
        try:
            result = json.loads(response)
            return {
                'classification': result.get('classification', 'unknown'),
                'confidence': result.get('confidence', 0.5),
                'reasoning': result.get('reasoning', ''),
                'source': 'ai'
            }
        except json.JSONDecodeError:
            logger.error("Failed to parse AI response")
            return {
                'classification': 'unknown',
                'confidence': 0.0,
                'reasoning': 'Parse error',
                'source': 'error'
            }
    
    def _fallback_url_classification(self, url: str) -> Dict:
        """Fallback keyword-based URL classification"""
        url_lower = url.lower()
        
        # Productive keywords
        productive = ['stackoverflow', 'github', 'docs', 'documentation', 'tutorial', 
                     'learn', 'course', 'education', 'wiki', 'research']
        
        # Distracting keywords
        distracting = ['youtube.com/shorts', 'tiktok', 'instagram', 'facebook', 
                      'twitter', 'reddit', 'netflix', 'twitch', 'gaming']
        
        for keyword in productive:
            if keyword in url_lower:
                return {
                    'classification': 'productive',
                    'confidence': 0.7,
                    'reasoning': f'Matched productive keyword: {keyword}',
                    'source': 'fallback'
                }
        
        for keyword in distracting:
            if keyword in url_lower:
                return {
                    'classification': 'distracting',
                    'confidence': 0.8,
                    'reasoning': f'Matched distracting keyword: {keyword}',
                    'source': 'fallback'
                }
        
        return {
            'classification': 'neutral',
            'confidence': 0.5,
            'reasoning': 'No clear indicators',
            'source': 'fallback'
        }
    
    def _fallback_app_classification(self, app_name: str, window_title: str) -> Dict:
        """Fallback keyword-based app classification"""
        combined = f"{app_name} {window_title}".lower()
        
        # Productive keywords
        productive = ['code', 'vscode', 'visual studio', 'pycharm', 'sublime', 
                     'notepad++', 'terminal', 'cmd', 'powershell', 'docs', 'word', 
                     'excel', 'notion', 'obsidian']
        
        # Distracting keywords
        distracting = ['steam', 'game', 'valorant', 'league', 'discord', 
                      'spotify', 'netflix', 'instagram', 'messenger']
        
        for keyword in productive:
            if keyword in combined:
                return {
                    'classification': 'productive',
                    'confidence': 0.7,
                    'reasoning': f'Matched productive keyword: {keyword}',
                    'source': 'fallback'
                }
        
        for keyword in distracting:
            if keyword in combined:
                return {
                    'classification': 'distracting',
                    'confidence': 0.8,
                    'reasoning': f'Matched distracting keyword: {keyword}',
                    'source': 'fallback'
                }
        
        return {
            'classification': 'neutral',
            'confidence': 0.5,
            'reasoning': 'No clear indicators',
            'source': 'fallback'
        }
    
    def clear_cache(self):
        """Clear classification cache"""
        self.cache = {}
        logger.info("Classification cache cleared")

# Singleton instance
_classifier_instance = None

def get_classifier() -> AIClassifier:
    """Get or create classifier instance"""
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = AIClassifier()
    return _classifier_instance

# Test
if __name__ == "__main__":
    classifier = AIClassifier()
    
    print("=== URL Classification Tests ===")
    
    # Test productive URLs
    urls = [
        "https://stackoverflow.com/questions/12345",
        "https://github.com/user/repo",
        "https://youtube.com/watch?v=tutorial",
        "https://instagram.com/explore",
        "https://twitter.com/feed"
    ]
    
    for url in urls:
        result = classifier.classify_url(url)
        print(f"\nURL: {url}")
        print(f"Classification: {result['classification']}")
        print(f"Confidence: {result['confidence']:.2f}")
        print(f"Reasoning: {result['reasoning']}")
        print(f"Source: {result['source']}")
    
    print("\n=== App Classification Tests ===")
    
    # Test apps
    apps = [
        ("vscode.exe", "main.py - Visual Studio Code"),
        ("chrome.exe", "Instagram - Google Chrome"),
        ("steam.exe", "Steam - Library")
    ]
    
    for app_name, window_title in apps:
        result = classifier.classify_app(app_name, window_title)
        print(f"\nApp: {app_name}")
        print(f"Title: {window_title}")
        print(f"Classification: {result['classification']}")
        print(f"Confidence: {result['confidence']:.2f}")
        print(f"Reasoning: {result['reasoning']}")
    
    print("\n✓ AI Classifier test complete!")

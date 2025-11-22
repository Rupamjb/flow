# Groq API Configuration for Flow Engine

## Setup Instructions

1. **Get Groq API Key**
   - Visit: https://console.groq.com/
   - Sign up for free account
   - Generate API key

2. **Set Environment Variable**
   ```bash
   # Windows (PowerShell)
   $env:GROQ_API_KEY="your_groq_api_key_here"
   
   # Or add to .env file
   GROQ_API_KEY=your_groq_api_key_here
   ```

3. **Install Dependencies**
   ```bash
   pip install requests python-dotenv
   ```

## Usage

The AI classifier will automatically use Groq API when configured:

```python
from ai_classifier import get_classifier

classifier = get_classifier()

# Classify URL
result = classifier.classify_url("https://youtube.com/watch?v=abc")
print(result['classification'])  # 'productive' or 'distracting'
print(result['reasoning'])        # AI's explanation
```

## Model Information

- **Model**: llama-3.1-8b-instant
- **Speed**: ~500 tokens/second
- **Cost**: Free tier available, then $0.05/1M tokens
- **Accuracy**: High for classification tasks

## Fallback Mode

If Groq API is not configured or fails, the system automatically falls back to keyword-based classification.

## Testing

```bash
# Test with Groq API
export GROQ_API_KEY=your_key
python backend/ai_classifier.py

# Test without API (fallback mode)
python backend/ai_classifier.py
```

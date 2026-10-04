import os
import sys
import requests
import dotenv

# Load .env file from project root or parent
_proj_env = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
if os.path.exists(_proj_env):
    dotenv.load_dotenv(_proj_env)
else:
    dotenv.load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env')))

def test_groq_ai():
    print("--- 1. Testing Groq API Key from .env ---")
    groq_key = os.getenv("GROQ_API_KEY")
    assert groq_key, "GROQ_API_KEY not found in .env"
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}
    payload = {
        "model": "qwen/qwen3.8-27b",
        "messages": [
            {"role": "system", "content": "You are an Agentium AI testing assistant."},
            {"role": "user", "content": "Briefly state that Groq AI integration is working."}
        ],
        "max_tokens": 50
    }
    
    resp = requests.post(url, headers=headers, json=payload, timeout=15)
    print("Groq HTTP Status:", resp.status_code)
    assert resp.status_code == 200, f"Groq request failed: {resp.text}"
    content = resp.json()["choices"][0]["message"]["content"]
    print("Groq AI Response:", content.strip())
    print("Groq Test: PASS\n")

def test_openrouter_ai():
    print("--- 2. Testing OpenRouter API Key from .env ---")
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    assert openrouter_key, "OPENROUTER_API_KEY not found in .env"
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {openrouter_key}", "Content-Type": "application/json"}
    payload = {
        "model": "meta-llama/llama-3.2-3b-instruct",
        "messages": [
            {"role": "system", "content": "You are an Agentium AI testing assistant."},
            {"role": "user", "content": "Briefly state that OpenRouter AI integration is working."}
        ],
        "max_tokens": 50
    }
    
    resp = requests.post(url, headers=headers, json=payload, timeout=15)
    print("OpenRouter HTTP Status:", resp.status_code)
    assert resp.status_code == 200, f"OpenRouter request failed: {resp.text}"
    content = resp.json()["choices"][0]["message"]["content"]
    print("OpenRouter AI Response:", content.strip())
    print("OpenRouter Test: PASS\n")

if __name__ == "__main__":
    print("=== Testing AI Keys from .env ===")
    test_groq_ai()
    test_openrouter_ai()
    print("All .env AI API Key Tests: PASS\n")

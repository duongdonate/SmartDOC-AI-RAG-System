#!/usr/bin/env python
"""Test kết nối từ LangChain đến Docker Ollama"""

import requests
from langchain_community.llms import Ollama

def test_direct_api():
    """Test trực tiếp API"""
    print("1. Testing direct API connection...")
    try:
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                'model': 'qwen2.5:1.5b',
                'prompt': 'Say "Hello"',
                'stream': False
            },
            timeout=10
        )
        if response.status_code == 200:
            print("   ✅ Direct API works!")
            return True
        else:
            print(f"   ❌ API error: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False

def test_langchain_ollama():
    """Test qua LangChain"""
    print("\n2. Testing LangChain Ollama integration...")
    try:
        llm = Ollama(
            model="qwen2.5:1.5b",
            base_url="http://localhost:11434",
            temperature=0.7
        )
        response = llm.invoke("Say 'Hello from LangChain'")
        print(f"   ✅ LangChain works! Response: {response[:50]}...")
        return True
    except Exception as e:
        print(f"   ❌ LangChain error: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing Docker Ollama connection\n")
    
    api_ok = test_direct_api()
    langchain_ok = test_langchain_ollama()
    
    if api_ok and langchain_ok:
        print("\n✅ All tests passed! Ollama is ready to use.")
    else:
        print("\n❌ Some tests failed. Check:")
        print("   - Is Ollama container running? 'docker ps | grep ollama'")
        print("   - Is model pulled? 'docker exec ollama ollama list'")
        print("   - Can you access http://localhost:11434?")
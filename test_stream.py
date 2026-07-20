import requests
import json

OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"

payload = {
    "model": "qwen2.5:14b",
    "messages": [
        {"role": "user", "content": "Włącz lampkę w salonie"}
    ],
    "tools": [
        {
            "type": "function",
            "function": {
                "name": "execute_ha_action",
                "description": "Wykonuje akcję w Home Assistant",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string"},
                        "entity_id": {"type": "string"}
                    }
                }
            }
        }
    ],
    "stream": True,
    "options": {"temperature": 0.0}
}

try:
    print("Sending request...")
    response = requests.post(OLLAMA_CHAT_URL, json=payload, stream=True)
    for line in response.iter_lines():
        if line:
            print(line.decode('utf-8'))
except Exception as e:
    print(f"Error: {e}")

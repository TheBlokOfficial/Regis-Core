import json
import logging
import requests
from core.exceptions import LLMConnectionError

class RemoteClient:
    def __init__(self, base_url: str = "http://192.168.0.119:8000"):
        self.base_url = base_url
        self.model_name = "Serwer Regis"
        self.tier = "remote"
        self.temperature = "N/A"
        
    def clear_history(self) -> None:
        try:
            requests.post(f"{self.base_url}/v1/clear_history", timeout=5)
        except requests.RequestException as e:
            logging.error(f"Nie udało się wyczyścić historii na serwerze: {e}")
            
    def generate_response(self, prompt: str, tools_registry, on_tool_call=None, on_thought_token=None, on_content_token=None) -> str:
        url = f"{self.base_url}/v1/chat/stream"
        payload = {"message": prompt}
        
        try:
            response = requests.post(url, json=payload, stream=True, timeout=300)
            response.raise_for_status()
            
            final_text = ""
            for line in response.iter_lines():
                if not line:
                    continue
                line = line.decode('utf-8')
                if line.startswith("data: "):
                    data_str = line[6:]
                    try:
                        event = json.loads(data_str)
                        ev_type = event.get("type")
                        content = event.get("content", "")
                        
                        if ev_type == "thought" and on_thought_token:
                            on_thought_token(content)
                        elif ev_type == "content" and on_content_token:
                            on_content_token(content)
                        elif ev_type == "tool" and on_tool_call:
                            on_tool_call(content)
                        elif ev_type == "done":
                            final_text = content
                        elif ev_type == "error":
                            logging.error(f"Serwer zwrócił błąd: {content}")
                            final_text = f"Błąd serwera: {content}"
                    except json.JSONDecodeError:
                        pass
                        
            return final_text
        except requests.RequestException as e:
            raise LLMConnectionError(f"Błąd połączenia z serwerem API ({self.base_url}): {e}")

    def generate_response_from_audio(self, audio_bytes: bytes, on_stt_result=None, on_tool_call=None, on_thought_token=None, on_content_token=None) -> str:
        url = f"{self.base_url}/v1/chat/audio_stream"
        
        try:
            files = {'file': ('audio.wav', audio_bytes, 'audio/wav')}
            response = requests.post(url, files=files, stream=True, timeout=300)
            response.raise_for_status()
            
            final_text = ""
            for line in response.iter_lines():
                if not line:
                    continue
                line = line.decode('utf-8')
                if line.startswith("data: "):
                    data_str = line[6:]
                    try:
                        event = json.loads(data_str)
                        ev_type = event.get("type")
                        content = event.get("content", "")
                        
                        if ev_type == "stt_result" and on_stt_result:
                            on_stt_result(content)
                        elif ev_type == "thought" and on_thought_token:
                            on_thought_token(content)
                        elif ev_type == "content" and on_content_token:
                            on_content_token(content)
                        elif ev_type == "tool" and on_tool_call:
                            on_tool_call(content)
                        elif ev_type == "done":
                            final_text = content
                        elif ev_type == "error":
                            logging.error(f"Serwer zwrócił błąd: {content}")
                            final_text = f"Błąd serwera: {content}"
                    except json.JSONDecodeError:
                        pass
                        
            return final_text
        except requests.RequestException as e:
            raise LLMConnectionError(f"Błąd połączenia z serwerem API (Audio): {e}")

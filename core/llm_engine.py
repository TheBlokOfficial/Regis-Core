import json
import logging
import requests
from requests.exceptions import RequestException
from typing import Any
import datetime

from core.exceptions import LLMConnectionError

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_GENERATE_URL = f"{OLLAMA_BASE_URL}/api/generate"
OLLAMA_CHAT_URL = f"{OLLAMA_BASE_URL}/api/chat"
OLLAMA_TAGS_URL = f"{OLLAMA_BASE_URL}/api/tags"

BASE_SYSTEM_PROMPT = """Jesteś inteligentnym administratorem domu o imieniu Regis. Twoim zadaniem jest zarządzanie systemem Home Assistant i dbanie o komfort mieszkańców.
Jesteś bezpośredni, proaktywny i decyzyjny. Kiedy użytkownik prosi o akcję (np. "włącz światła"), wykonuj ją od razu – nie dopytuj o pozwolenie ani potwierdzenie dla oczywistych poleceń.
Masz do dyspozycji zestaw narzędzi (Tool Calling). Używaj ich zgodnie z własnym osądem, aby diagnozować stan urządzeń i realizować zlecenia. Pamiętaj: sama Twoja odpowiedź tekstowa nie wpływa na dom. Aby coś włączyć/wyłączyć, musisz fizycznie wywołać narzędzie (Tool Call). Nigdy nie informuj o wykonaniu akcji, jeśli najpierw nie uruchomiłeś narzędzia.
Jedyna techniczna reguła: system fizyczny wymaga dokładnych identyfikatorów (entity_id) do wykonania akcji. Jeśli ich jeszcze nie znasz dla danego urządzenia, odszukaj je przy pomocy odpowiednich narzędzi przed wydaniem komendy wykonawczej.
Po zakończeniu zadania poinformuj użytkownika o rezultacie w naturalny, zwięzły sposób (po polsku)."""

TIER_RULES = {
    "basic": "Działasz w trybie ograniczonym (Basic). Jeśli użytkownik prosi o zaawansowaną analizę, poinformuj go, że Twoja wersja modelu jest na to za słaba.",
    "advanced": "Jesteś zaawansowaną AI o dużej swobodzie decyzyjnej. Proaktywnie zarządzaj domem, przewiduj potrzeby i proponuj optymalizacje."
}

class LLMEngine:
    """Silnik odpowiadający za komunikację z lokalnym serwerem Ollama."""

    def __init__(self, model_name: str, tier: str, temperature: float = 0.5, history_limit: int = 10):
        """Inicjalizuje silnik z odpowiednim modelem.
        
        Args:
            model_name (str): Nazwa modelu używanego w Ollamie.
            tier (str): Klasa modelu (np. basic lub advanced).
            temperature (float): Poziom losowości generowanych odpowiedzi.
            history_limit (int): Maksymalna liczba pamiętanych wiadomości.
        """
        self.model_name = model_name
        self.tier = tier
        self.temperature = temperature
        self.history_limit = history_limit
        self.history = []
        logging.info(f"Zainicjalizowano LLMEngine: Model={model_name}, Tier={self.tier}, Temp={temperature}, HistoryLimit={history_limit}")

    @staticmethod
    def get_available_models() -> list[str]:
        """Pobiera z lokalnej instancji Ollamy listę dostępnych modeli.
        
        Returns:
            list[str]: Lista pobranych modeli.
        Raises:
            LLMConnectionError: Gdy nie można nawiązać połączenia z serwerem Ollama.
        """
        try:
            response = requests.get(OLLAMA_TAGS_URL, timeout=5)
            response.raise_for_status()
            data = response.json()
            models = [model['name'] for model in data.get('models', [])]
            return models
        except RequestException as e:
            logging.error(f"Nie można połączyć się z serwerem Ollama: {e}")
            raise LLMConnectionError(f"Ollama API Error: {e}")

    def clear_history(self) -> None:
        """Czyszczenie lokalnej historii konwersacji."""
        self.history = []
        logging.info("Wyczyszczono historię konwersacji LLM.")

    def _parse_fallback_tool_calls(self, response_text: str, valid_tools: list[str], status_callback: Any = None) -> tuple[list[dict], str]:
        """Próbuje wyciągnąć zgubione wywołania narzędzi z surowego tekstu odpowiedzi."""
        tool_calls = []
        extracted_jsons = []
        stack = []
        start_idx = -1
        for i, char in enumerate(response_text):
            if char == '{':
                if not stack:
                    start_idx = i
                stack.append(char)
            elif char == '}':
                if stack:
                    stack.pop()
                    if not stack:
                        json_str = response_text[start_idx:i+1]
                        try:
                            parsed = json.loads(json_str)
                            if isinstance(parsed, dict):
                                extracted_jsons.append((parsed, start_idx, i+1))
                        except json.JSONDecodeError:
                            pass
        
        message_content = response_text
        for parsed, start_idx, end_idx in extracted_jsons:
            matched_func = None
            matched_args = None
            cut_start = start_idx
            
            # Wzorzec A: OpenAI ({"name": "...", "arguments": {...}})
            if "name" in parsed and "arguments" in parsed and parsed["name"] in valid_tools:
                matched_func = parsed["name"]
                matched_args = parsed["arguments"]
            
            # Wzorzec B: Qwen2.5 / Mistral (nazwa_funkcji {...})
            else:
                prefix = message_content[:start_idx].strip().split()
                if prefix:
                    potential_func = prefix[-1]
                    if potential_func in valid_tools:
                        matched_func = potential_func
                        matched_args = parsed
                        cut_start = message_content.rfind(potential_func, 0, start_idx)
            
            if matched_func:
                tool_calls.append({
                    "function": {
                        "name": matched_func,
                        "arguments": matched_args
                    }
                })
                logging.warning(f"Zastosowano Fallback Parsowania dla narzędzia: {matched_func}")
                if status_callback:
                    status_callback(f"[dim]⚠ Użyto fallbacku parsowania dla {matched_func}...[/dim]")
                    
                # Czyszczenie przecieku z tekstu (TTS protection)
                cleaned_text = message_content[:cut_start] + message_content[end_idx:]
                # Oczyszczenie z resztek markdowna lub śmieciowych znaczników Qwen
                cleaned_text = cleaned_text.replace("lashes", "").replace("```json", "").replace("```", "").replace("URING", "").strip()
                message_content = cleaned_text
                break
                
        return tool_calls, message_content

    def generate_response(self, prompt: str, tools_registry, status_callback: Any = None, stream_callback: Any = None) -> str:
        """Generuje zapytanie do modelu LLM z użyciem narzędzi i historii.
        
        Args:
            prompt (str): Polecenie od użytkownika.
            tools_registry: Instancja rejestru narzędzi.
            status_callback (callable): Funkcja wywoływana z informacją o używanych narzędziach.
            stream_callback (callable): Funkcja wywoływana z każdym nowym tokenem tekstu.
            
        Returns:
            str: Tekstowa odpowiedź od modelu.
        Raises:
            LLMConnectionError: Jeśli wygenerowanie odpowiedzi się nie powiodło.
        """
        prompt_to_use = f"{BASE_SYSTEM_PROMPT}\n{TIER_RULES.get(self.tier, TIER_RULES['basic'])}"
        messages = [{"role": "system", "content": prompt_to_use}]
        # Przekazujemy do Ollamy tylko pola role i content, ucinając nasz wewnętrzny timestamp oraz ignorując customowe role
        messages.extend([{"role": m["role"], "content": m["content"]} for m in self.history if m["role"] not in ["tool_log"]])
        messages.append({"role": "user", "content": prompt})
        
        now = datetime.datetime.now().strftime("%H:%M:%S")
        self.history.append({"role": "user", "content": prompt, "timestamp": now})
        
        while True:
            payload = {
                "model": self.model_name,
                "messages": messages,
                "stream": True,
                "tools": tools_registry.tools_schema,
                "options": {
                    "temperature": self.temperature,
                    "num_ctx": 4096
                }
            }
            
            try:
                response = requests.post(OLLAMA_CHAT_URL, json=payload, timeout=30, stream=True)
                response.raise_for_status()
                
                full_content = ""
                tool_calls_accumulator = []
                
                for line in response.iter_lines():
                    if not line:
                        continue
                    chunk = json.loads(line)
                    msg_chunk = chunk.get("message", {})
                    
                    if "content" in msg_chunk and msg_chunk["content"]:
                        piece = msg_chunk["content"]
                        full_content += piece
                        if stream_callback:
                            stream_callback(piece)
                            
                    if "tool_calls" in msg_chunk:
                        tool_calls_accumulator.extend(msg_chunk["tool_calls"])
                        
                message = {"role": "assistant", "content": full_content}
                if tool_calls_accumulator:
                    message["tool_calls"] = tool_calls_accumulator
                
                messages.append(message)
                
                tool_calls = message.get("tool_calls", [])
                response_text = message.get("content", "")
                
                # Fallback: ręczne wyciąganie wywołania narzędzia, gdy model zignoruje natywne API
                if not tool_calls and response_text:
                    valid_tools = [t["function"]["name"] for t in tools_registry.tools_schema]
                    extracted_tool_calls, cleaned_text = self._parse_fallback_tool_calls(response_text, valid_tools, status_callback)
                    if extracted_tool_calls:
                        tool_calls = extracted_tool_calls
                        message["content"] = cleaned_text

                if tool_calls:
                    for tool_call in tool_calls:
                        function_name = tool_call["function"]["name"]
                        arguments = tool_call["function"]["arguments"]
                        
                        if status_callback:
                            status_callback(f"> Regis używa narzędzia: {function_name}...")
                            
                        now_tool = datetime.datetime.now().strftime("%H:%M:%S")
                        self.history.append({
                            "role": "tool_log",
                            "content": f"> Regis używa narzędzia: {function_name}...",
                            "timestamp": now_tool
                        })
                            
                        if isinstance(arguments, str):
                            try:
                                arguments = json.loads(arguments)
                            except json.JSONDecodeError:
                                arguments = {}
                                
                        tool_result = tools_registry.execute_tool(function_name, arguments)
                        
                        messages.append({
                            "role": "tool",
                            "content": tool_result
                        })
                else:
                    response_text = message.get("content", "")
                    now_assistant = datetime.datetime.now().strftime("%H:%M:%S")
                    self.history.append({"role": "assistant", "content": response_text, "timestamp": now_assistant})
                    
                    if len(self.history) > self.history_limit:
                        self.history = self.history[-self.history_limit:]
                        
                    return response_text
                    
            except RequestException as e:
                error_details = str(e)
                if hasattr(e, 'response') and e.response is not None:
                    try:
                        error_details = f"{e} - {e.response.json().get('error', e.response.text)}"
                    except Exception:
                        error_details = f"{e} - {e.response.text}"
                logging.error(f"Ollama Chat Error: {error_details}")
                raise LLMConnectionError(f"Odrzucono zapytanie (HTTP Error): {error_details}")

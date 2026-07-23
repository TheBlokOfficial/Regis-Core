import json
import logging
import requests
from requests.exceptions import RequestException
from typing import Any
import datetime

from core.exceptions import LLMConnectionError
from core.stream_parser import StreamingTokenParser
from core.schemas import BASE_TOOLS_SCHEMA, render_tools_for_prompt
from core import config


class LLMEngine:
    """Silnik odpowiadający za komunikację z lokalnym serwerem Ollama.
    
    Architektura Droga A: pełna kontrola nad tool callingiem.
    Opisy narzędzi są renderowane do tekstu promptu systemowego,
    a nie wysyłane jako pole 'tools' do API Ollamy (co eliminuje
    kolizję z natywnym angielskim blokiem instrukcji Ollamy).
    """

    def __init__(self, model_name: str, tier: str, temperature: float = 0.1, history_limit: int = 20):
        """Inicjalizuje silnik z odpowiednim modelem.
        
        Args:
            model_name: Nazwa modelu w Ollamie.
            tier: Klasa modelu (butler, regis, prime).
            temperature: Poziom losowości (0.1 dla tool callingu).
            history_limit: Maksymalna liczba zapamiętanych TUR konwersacji (par user+assistant).
        """
        self.model_name = model_name
        self.tier = tier
        self.temperature = temperature
        self.history_limit = history_limit
        self.history = []  # Lista kompletnych tur: [{"user": str, "assistant": str, "timestamp": str}]
        logging.info(f"Zainicjalizowano LLMEngine: Model={model_name}, Tier={self.tier}, Temp={temperature}, TurnLimit={history_limit}")

    @staticmethod
    def get_available_models() -> list[str]:
        """Pobiera z lokalnej instancji Ollamy listę dostępnych modeli."""
        settings = config.load_settings()
        tags_url = f"{settings.get('ollama_url', 'http://127.0.0.1:11434')}/api/tags"
        try:
            response = requests.get(tags_url, timeout=5)
            response.raise_for_status()
            data = response.json()
            return [model['name'] for model in data.get('models', [])]
        except RequestException as e:
            logging.error(f"Nie można połączyć się z serwerem Ollama: {e}")
            raise LLMConnectionError(f"Ollama API Error: {e}")

    def _build_system_prompt(self) -> str:
        """Buduje kompletny system prompt: tier + narzędzia + baza.
        
        Droga A: zamiast wysyłać pole 'tools' do API (co powoduje
        wstrzyknięcie przez Ollamę własnego angielskiego bloku instrukcji),
        renderujemy opisy narzędzi bezpośrednio do tekstu w formacie
        natywnym dla Qwen 2.5 (tagi <tools>).
        """
        import os
        tier_path = os.path.join("data", "prompts", f"tier_{self.tier}.md")
        
        tier_prompt = "Jesteś asystentem domowym."
        
        try:
            with open(tier_path, "r", encoding="utf-8") as f:
                tier_prompt = f.read().strip()
        except Exception as e:
            logging.warning(f"Błąd ładowania {tier_path}: {e}")
            
        # Dla tieru butler (parser NLU) nie wstrzykujemy tagów <tools> ani reguł Sandwiching, 
        # bo to czysty ekstraktor JSON bazujący na własnym prompcie.
        if self.tier == "butler":
            return tier_prompt

        # Renderowanie narzędzi do tekstu (format Hermes/Qwen) dla innych tierów
        tools_text = render_tools_for_prompt(self.tier)
        
        # Twardy przypominacz zwalczający utratę instrukcji w modelu 7B (Sandwiching)
        critical_rules = (
            "KRYTYCZNE ZASADY BEHAWIORALNE:\n"
            "Zawsze otwieraj znacznik <thought> jako pierwszą rzecz w swojej odpowiedzi, aby zaplanować działanie. "
            "Nigdy nie generuj od razu czystego tekstu odpowiedzi. Nigdy nie wymyślaj danych, których "
            "nie pobrałeś odpowiednim narzędziem z bloku <tools>."
        )
        
        return f"{tier_prompt}\n\n{tools_text}\n\n{critical_rules}"

    def clear_history(self) -> None:
        """Czyszczenie historii konwersacji."""
        self.history = []
        logging.info("Wyczyszczono historię konwersacji LLM.")

    def _parse_tool_call_from_text(self, response_text: str) -> tuple[dict | None, str]:
        """Parsuje wywołanie narzędzia z tekstu odpowiedzi.
        
        Szuka pierwszego bloku <tool_call>...</tool_call> lub luźnego JSONa
        pasującego do znanego narzędzia. Zwraca (tool_call, oczyszczony_tekst)
        lub (None, oryginalny_tekst) jeśli nie znaleziono.
        """
        import re
        
        all_known_tools = [t["function"]["name"] for t in BASE_TOOLS_SCHEMA]
        
        # Metoda 1: szukaj jawnego bloku <tool_call>...</tool_call>
        tag_match = re.search(r'<tool_call>\s*(\{.*?\})\s*(?:</tool_call>)?', response_text, re.DOTALL)
        if tag_match:
            try:
                parsed = json.loads(tag_match.group(1))
                func_name = parsed.get("name", "")
                func_args = parsed.get("arguments", {})
                if func_name in all_known_tools:
                    cleaned = response_text[:tag_match.start()].strip()
                    # Czyścimy resztki tagów
                    cleaned = cleaned.replace("<tool_call>", "").replace("</tool_call>", "").strip()
                    return {"function": {"name": func_name, "arguments": func_args}}, cleaned
            except json.JSONDecodeError:
                logging.warning(f"Znaleziono blok <tool_call>, ale JSON jest nieprawidłowy: {tag_match.group(1)[:100]}")
        
        # Metoda 2: fallback — szukaj luźnego JSONa z polem "name" pasującym do narzędzia
        stack = []
        start_idx = -1
        in_string = False
        escape_next = False
        extracted_jsons = []
        
        for i, char in enumerate(response_text):
            if escape_next:
                escape_next = False
                continue
            if char == '\\':
                escape_next = True
                continue
            if char == '"':
                in_string = not in_string
                continue
            if not in_string:
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
                                if isinstance(parsed, dict) and parsed.get("name") in all_known_tools:
                                    extracted_jsons.append((parsed, start_idx, i+1))
                            except json.JSONDecodeError:
                                pass
        
        if extracted_jsons:
            parsed, start_idx, end_idx = extracted_jsons[0]
            func_name = parsed["name"]
            func_args = parsed.get("arguments", {})
            cleaned = response_text[:start_idx].strip()
            cleaned = cleaned.replace("<tool_call>", "").replace("</tool_call>", "").replace("```json", "").replace("```", "").strip()
            logging.warning(f"Zastosowano fallback parsowania dla narzędzia: {func_name}")
            return {"function": {"name": func_name, "arguments": func_args}}, cleaned
        
        return None, response_text

    def generate_response(self, prompt: str, tools_registry, on_tool_call: Any = None, on_thought_token: Any = None, on_content_token: Any = None) -> str:
        """Generuje odpowiedź modelu z użyciem narzędzi i historii.
        
        Args:
            prompt: Polecenie od użytkownika.
            tools_registry: Instancja rejestru narzędzi.
            on_tool_call: Callback użycia narzędzia.
            on_thought_token: Callback tokenu myśli.
            on_content_token: Callback tokenu treści.
            
        Returns:
            Tekstowa odpowiedź od modelu.
        """
        prompt_to_use = self._build_system_prompt()
        messages = [{"role": "system", "content": prompt_to_use}]

        # Budowanie historii z kompletnych tur (user + assistant)
        for turn in self.history:
            messages.append({"role": "user", "content": f"[{turn['timestamp']}] {turn['user']}"})
            messages.append({"role": "assistant", "content": turn['assistant']})

        # Nowe zapytanie użytkownika
        now = datetime.datetime.now().strftime("%H:%M:%S")
        
        # Dla NLU parsera (butler) przedrostek czasu może mylić model
        if self.tier == "butler":
            messages.append({"role": "user", "content": prompt})
        else:
            messages.append({"role": "user", "content": f"[{now}] {prompt}"})
        
        parser = StreamingTokenParser(on_thought_token, on_content_token)

        # FAST PATH: Butler jako NLU (Structured Outputs)
        if self.tier == "butler":
            return self._generate_response_nlu(messages, prompt, tools_registry, on_tool_call, on_content_token)

        settings = config.load_settings()
        chat_url = f"{settings.get('ollama_url', 'http://127.0.0.1:11434')}/api/chat"

        # Pętla ReAct
        max_iterations = 15
        iteration_count = 0
        while iteration_count < max_iterations:
            iteration_count += 1
            parser.reset_state()
            
            # Droga A: BEZ pola 'tools' w payloadzie.
            # Opisy narzędzi są w system prompcie. Model generuje <tool_call> w tekście.
            payload = {
                "model": self.model_name,
                "messages": messages,
                "stream": True,
                "keep_alive": -1,
                "options": {
                    "temperature": self.temperature,
                    "num_ctx": 8192,
                    "top_p": 0.8,
                    "repeat_penalty": 1.05,
                    "num_predict": 1536,
                    "stop": ["</tool_call>", "</tool_call >"]
                }
            }

            try:
                response = requests.post(chat_url, json=payload, timeout=300, stream=True)
                response.raise_for_status()

                full_content = ""

                for line in response.iter_lines():
                    if not line:
                        continue
                    chunk = json.loads(line)
                    msg_chunk = chunk.get("message", {})

                    if "content" in msg_chunk and msg_chunk["content"]:
                        piece = msg_chunk["content"]
                        full_content += piece
                        parser.feed_token(piece)

                response_text = full_content

                # Parsowanie tool_call z tekstu (jedyna ścieżka w Drodze A)
                tool_call, cleaned_text = self._parse_tool_call_from_text(response_text)

                # Dodaj odpowiedź asystenta do messages (dla kontynuacji pętli)
                messages.append({"role": "assistant", "content": response_text})

                if tool_call:
                    function_name = tool_call["function"]["name"]
                    arguments = tool_call["function"]["arguments"]

                    if isinstance(arguments, str):
                        try:
                            arguments = json.loads(arguments)
                        except json.JSONDecodeError:
                            arguments = {"raw_args": arguments}
                    if not isinstance(arguments, dict):
                        arguments = {"raw_payload": str(arguments)}

                    # Log narzędzia dla UI
                    args_str = ", ".join(f"{k}={v}" for k, v in arguments.items())
                    log_text = f"> Regis używa: {function_name}({args_str})"
                    if on_tool_call:
                        on_tool_call(log_text)

                    # Wykonanie narzędzia
                    tool_result = tools_registry.execute_tool(function_name, arguments)

                    # Wynik narzędzia trafia do messages jako role: tool
                    messages.append({"role": "tool", "content": tool_result})

                else:
                    # Brak tool_call — to jest finalna odpowiedź
                    # Kondensacja: zapisz tylko user+assistant do trwałej historii
                    self.history.append({
                        "user": prompt,
                        "assistant": response_text,
                        "timestamp": now
                    })

                    # Przycinanie historii (po pełnych turach, nie krokach ReAct)
                    if self.history_limit <= 0:
                        self.history = []
                    elif len(self.history) > self.history_limit:
                        self.history = self.history[-self.history_limit:]

                    return response_text

            except RequestException as e:
                error_details = str(e)
                logging.error(f"Błąd połączenia LLMEngine: {error_details}")
                raise LLMConnectionError(f"Nie udało się połączyć z usługą. {error_details}")
        
        return "Przerwano zapytanie. Przekroczono maksymalną liczbę wywołań narzędzi (timeout pętli ReAct)."

    def _generate_response_nlu(self, messages: list[dict], original_prompt: str, tools_registry, on_tool_call: Any, on_content_token: Any) -> str:
        """Szybka ścieżka generacji dla tieru 'butler'.
        Używa Structured Outputs (JSON Schema), aby jednym zapytaniem wydobyć intencję.
        Brak pętli ReAct, całkowicie deterministyczne wyjście.
        """
        settings = config.load_settings()
        chat_url = f"{settings.get('ollama_url', 'http://127.0.0.1:11434')}/api/chat"

        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "keep_alive": -1,
            "format": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["light_on", "light_off", "set_brightness", "unknown"]},
                    "room": {"type": ["string", "null"]},
                    "brightness_value": {"type": ["integer", "null"]},
                    "brightness_direction": {"type": ["string", "null"], "enum": ["up", "down", None]}
                },
                "required": ["action", "room", "brightness_value", "brightness_direction"]
            },
            "options": {
                "temperature": 0.0,
                "num_predict": 80
            }
        }
        
        try:
            response = requests.post(chat_url, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            content = data.get("message", {}).get("content", "{}")
            
            try:
                intent = json.loads(content)
            except json.JSONDecodeError:
                intent = {"action": "unknown"}
                
            action = intent.get("action", "unknown")
            room = intent.get("room")
            
            if action == "unknown":
                if on_content_token:
                    on_content_token("Przepraszam, to polecenie wykracza poza moje uprawnienia (zarządzam tylko oświetleniem).")
                return "Przepraszam, to polecenie wykracza poza moje uprawnienia (zarządzam tylko oświetleniem)."
                
            # Logika mapowania intencji na wywołanie Home Assistant
            target_entity = f"light.{room}" if room and room not in ["pokój", "pokoju"] else "light.moj_pokoj"
            
            ha_action = None
            if action == "light_on":
                ha_action = "turn_on"
            elif action == "light_off":
                ha_action = "turn_off"
            elif action == "set_brightness":
                ha_action = "turn_on"
                
            if ha_action:
                tool_args = {"action": ha_action, "entity_id": target_entity, "parameters": {}}
                args_str = f"action='{ha_action}', entity_id='{target_entity}'"
                
                if intent.get("brightness_value") is not None:
                    tool_args["parameters"]["brightness_pct"] = intent["brightness_value"]
                    args_str += f", brightness_pct={intent['brightness_value']}"
                elif intent.get("brightness_direction") == "up":
                    # Krok +20% (implementacja uproszczona jako step w HA)
                    tool_args["parameters"]["brightness_step_pct"] = 20
                    args_str += f", brightness_step_pct=20"
                elif intent.get("brightness_direction") == "down":
                    # Krok -20% 
                    tool_args["parameters"]["brightness_step_pct"] = -20
                    args_str += f", brightness_step_pct=-20"
                    
                log_text = f"> Lokaj (NLU) wywołuje: execute_ha_action({args_str})"
                if on_tool_call:
                    on_tool_call(log_text)
                    
                tools_registry.execute_tool("execute_ha_action", tool_args)
                
            if on_content_token:
                on_content_token("Gotowe.")
            return "Gotowe."
            
        except RequestException as e:
            logging.error(f"Błąd NLU: {e}")
            return "Błąd komunikacji z modułem NLU."

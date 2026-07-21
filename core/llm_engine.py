import json
import logging
import requests
from requests.exceptions import RequestException
from typing import Any
import datetime

from core.exceptions import LLMConnectionError
from core.stream_parser import StreamingTokenParser
from core.schemas import BASE_TOOLS_SCHEMA

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_GENERATE_URL = f"{OLLAMA_BASE_URL}/api/generate"
OLLAMA_CHAT_URL = f"{OLLAMA_BASE_URL}/api/chat"
OLLAMA_TAGS_URL = f"{OLLAMA_BASE_URL}/api/tags"


class LLMEngine:
    """Silnik odpowiadający za komunikację z lokalnym serwerem Ollama."""

    def __init__(self, model_name: str, tier: str, temperature: float = 0.4, history_limit: int = 10):
        """Inicjalizuje silnik z odpowiednim modelem.
        
        Args:
            model_name (str): Nazwa modelu używanego w Ollamie.
            tier (str): Klasa modelu (np. butler lub regis).
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

    def _build_system_prompt(self) -> str:
        """Dynamicznie wczytuje prompt bazowy i warstwy z plików."""
        import os
        base_path = os.path.join("data", "prompts", "base_system.md")
        tier_path = os.path.join("data", "prompts", f"tier_{self.tier}.md")
        
        base_prompt = "Jesteś asystentem domowym."
        tier_prompt = "Wykonujesz polecenia."
        
        try:
            with open(base_path, "r", encoding="utf-8") as f:
                base_prompt = f.read().strip()
        except Exception as e:
            logging.warning(f"Błąd ładowania {base_path}: {e}")
            
        try:
            with open(tier_path, "r", encoding="utf-8") as f:
                tier_prompt = f.read().strip()
        except Exception as e:
            logging.warning(f"Błąd ładowania {tier_path}: {e}")
            
        sandwich = "\n\n## KRYTYCZNE ZASADY BEHAWIORALNE (PRZYPOMNIENIE)\n- Zanim wywołasz narzędzie lub powiesz cokolwiek, ZAWSZE wygeneruj swój monolog zaczynający się od `<thought>` i kończący się na `</thought>`.\n- Po zamknięciu myśli zachowaj ABSOLUTNĄ CISZĘ i wygeneruj od razu czystą strukturę `<tool_call>` (żadnego tekstu w stylu 'Dobrze, sprawdzam').\n- Narzędzi używaj ściśle wedle wytycznych i zawsze naprawiaj własne błędy, jeśli JSON zwróci error."
        return f"{tier_prompt}\n\n{base_prompt}{sandwich}"

    def clear_history(self) -> None:
        """Czyszczenie lokalnej historii konwersacji."""
        self.history = []
        logging.info("Wyczyszczono historię konwersacji LLM.")

    def _parse_fallback_tool_calls(self, response_text: str, valid_tools: list[str]) -> tuple[list[dict], str]:
        """Próbuje wyciągnąć zgubione wywołania narzędzi z surowego tekstu odpowiedzi, uwzględniając znaki ucieczki i stringi."""
        tool_calls = []
        extracted_jsons = []
        
        # Fuzzy JSON repair: parser stosowy odporny na cudzysłowy w tekście
        stack = []
        start_idx = -1
        in_string = False
        escape_next = False
        
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
                                if isinstance(parsed, dict):
                                    extracted_jsons.append((parsed, start_idx, i+1))
                            except json.JSONDecodeError:
                                pass
        
        message_content = response_text
        cuts = []
        all_known_tools = [t["function"]["name"] for t in BASE_TOOLS_SCHEMA]

        for parsed, start_idx, end_idx in extracted_jsons:
            matched_func = None
            matched_args = None
            cut_start = start_idx
            
            # Wzorzec A: OpenAI
            if "name" in parsed and "arguments" in parsed and parsed["name"] in all_known_tools:
                matched_func = parsed["name"]
                matched_args = parsed["arguments"]
            
            # Wzorzec B: Qwen2.5 / Mistral
            else:
                prefix = message_content[:start_idx].strip().split()
                if prefix:
                    potential_func = prefix[-1]
                    if potential_func in all_known_tools:
                        matched_func = potential_func
                        matched_args = parsed
                        found_idx = message_content.rfind(potential_func, 0, start_idx)
                        if found_idx != -1:
                            cut_start = found_idx
            
            if matched_func:
                tool_calls.append({
                    "function": {
                        "name": matched_func,
                        "arguments": matched_args
                    }
                })
                cuts.append((cut_start, end_idx))
                logging.warning(f"Zastosowano Fallback Parsowania dla narzędzia: {matched_func}")
                break # Bierzemy tylko pierwsze wywołanie!

        # Jeśli znaleziono narzędzie, ucinamy tekst na początku jego wywołania, aby pozbyć się halucynacji "parallel tool calling" i zachować tylko thought.
        if cuts:
            c_start, c_end = cuts[0]
            message_content = message_content[:c_start]

        # Oczyszczenie ze zbędnych śmieci
        message_content = message_content.replace("</tool_call>", "").replace("<tool_call>", "").replace("```json", "").replace("```", "").strip()
        
        return tool_calls, message_content

    def generate_response(self, prompt: str, tools_registry, on_tool_call: Any = None, on_thought_token: Any = None, on_content_token: Any = None) -> str:
        """Generuje zapytanie do modelu LLM z użyciem narzędzi i historii.
        
        Args:
            prompt (str): Polecenie od użytkownika.
            tools_registry: Instancja rejestru narzędzi.
            on_tool_call (callable): Zdarzenie użycia narzędzia.
            on_thought_token (callable): Zdarzenie tokenu myśli.
            on_content_token (callable): Zdarzenie tokenu treści.
            
        Returns:
            str: Tekstowa odpowiedź od modelu.
        """
        if hasattr(tools_registry, 'tick_desk'):
            tools_registry.tick_desk()
            
        prompt_to_use = self._build_system_prompt()
        messages = [{"role": "system", "content": prompt_to_use}]

        for m in self.history:
            if m["role"] not in ["tool_log"]:
                msg_dict = {"role": m["role"], "content": m.get("content", "")}
                if "tool_calls" in m:
                    msg_dict["tool_calls"] = m["tool_calls"]
                if m["role"] == "user" and "timestamp" in m:
                    msg_dict["content"] = f"[{m['timestamp']}] {msg_dict['content']}"
                messages.append(msg_dict)

        now = datetime.datetime.now().strftime("%H:%M:%S")
        messages.append({"role": "user", "content": f"[{now}] {prompt}"})
        self.history.append({"role": "user", "content": prompt, "timestamp": now})
        
        parser = StreamingTokenParser(on_thought_token, on_content_token)

        # Pętla ReAct — domyślnie każda to faza reasoning (narzędziowa).
        max_iterations = 15
        iteration_count = 0
        while iteration_count < max_iterations:
            iteration_count += 1
            parser.reset_state()
            
            # Wzorzec Open/Close: Wstrzykiwanie aktualnego stanu otwartych aplikacji na biurku
            try:
                desk_state_content = tools_registry.get_desk_state() if hasattr(tools_registry, 'get_desk_state') else ""
            except Exception as e:
                logging.error(f"Krytyczny błąd pobierania stanu biurka: {e}")
                desk_state_content = f"Wystąpił błąd podczas sprawdzania biurka: {e}"
                
            if not desk_state_content:
                desk_state_content = "Biurko jest puste."
                    
            state_injection = {
                "role": "system",
                "content": f"<desk_state>\n{desk_state_content}\n</desk_state>"
            }
            
            # Bezpieczna kopia wiadomości, do której na sam dół dodajemy świeży stan
            current_messages = messages.copy()
            current_messages.append(state_injection)
            
            payload = {
                "model": self.model_name,
                "messages": current_messages,
                "tools": tools_registry.tools_schema,
                "stream": True,
                "options": {
                    "temperature": self.temperature,
                    "num_ctx": 4096,
                    "top_p": 0.8,
                    "repeat_penalty": 1.05,
                    "num_predict": 512,
                    "stop": ["</tool_call>", "</tool_call >"]
                }
            }

            try:
                response = requests.post(OLLAMA_CHAT_URL, json=payload, timeout=120, stream=True)
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
                        parser.feed_token(piece)

                    if "tool_calls" in msg_chunk:
                        tool_calls_accumulator.extend(msg_chunk["tool_calls"])

                response_text = full_content

                if not tool_calls_accumulator and response_text:
                    valid_tools = [t["function"]["name"] for t in tools_registry.tools_schema]
                    extracted_tool_calls, cleaned_text = self._parse_fallback_tool_calls(response_text, valid_tools)
                    if extracted_tool_calls:
                        tool_calls_accumulator = extracted_tool_calls
                        response_text = cleaned_text
                        full_content = cleaned_text

                if tool_calls_accumulator and len(tool_calls_accumulator) > 1:
                    logging.warning(f"Zablokowano równoległe wywołania narzędzi. Odcięto {len(tool_calls_accumulator) - 1} narzędzi.")
                    tool_calls_accumulator = [tool_calls_accumulator[0]]

                message = {"role": "assistant", "content": full_content}
                if tool_calls_accumulator:
                    message["tool_calls"] = tool_calls_accumulator
                messages.append(message)

                if tool_calls_accumulator:
                    now_assistant = datetime.datetime.now().strftime("%H:%M:%S")
                    history_assistant_msg = message.copy()
                    history_assistant_msg["timestamp"] = now_assistant
                    history_assistant_msg["is_internal"] = True
                    self.history.append(history_assistant_msg)

                    for tool_call in tool_calls_accumulator:
                        function_name = tool_call["function"]["name"]
                        arguments = tool_call["function"]["arguments"]

                        if isinstance(arguments, str):
                            try:
                                args_dict = json.loads(arguments)
                            except json.JSONDecodeError:
                                args_dict = {"raw_args": arguments}
                        else:
                            args_dict = arguments
                            
                        if not isinstance(args_dict, dict):
                            args_dict = {"raw_payload": str(args_dict)}

                        args_str = ", ".join(f"{k}={v}" for k, v in args_dict.items())
                        log_text = f"> Regis używa: {function_name}({args_str})"

                        if on_tool_call:
                            on_tool_call(log_text)

                        now_tool = datetime.datetime.now().strftime("%H:%M:%S")
                        self.history.append({
                            "role": "tool_log",
                            "content": log_text,
                            "timestamp": now_tool
                        })

                        arguments = args_dict
                        tool_result = tools_registry.execute_tool(function_name, arguments)

                        tool_msg = {"role": "tool", "content": tool_result}
                        messages.append(tool_msg)

                        history_tool_msg = tool_msg.copy()
                        history_tool_msg["is_internal"] = True
                        self.history.append(history_tool_msg)

                else:
                    response_text = message.get("content", "")
                    now_assistant = datetime.datetime.now().strftime("%H:%M:%S")
                    self.history.append({"role": "assistant", "content": response_text, "timestamp": now_assistant})

                    if len(self.history) > self.history_limit:
                        self.history = self.history[-self.history_limit:]

                    return response_text

            except RequestException as e:
                # Wycofanie wiadomości użytkownika z historii połączenia w razie błędu sieci, by zapobiec spiętrzaniu asymetrycznemu
                if self.history and self.history[-1]["role"] == "user":
                    self.history.pop()
                    
                error_details = str(e)
                logging.error(f"Błąd połączenia LLMEngine: {error_details}")
                raise LLMConnectionError(f"Nie udało się połączyć z usługą. {error_details}")
        
        return "Przerwano zapytanie. Przekroczono maksymalną liczbę wywołań wewnętrznych narzędzi w systemie (Timeout pętli)."

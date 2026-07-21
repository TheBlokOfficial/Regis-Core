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
            
        return f"{base_prompt}\n{tier_prompt}"

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
                # Musimy użyć regex lub string replace uważnie, ponieważ indeksy mogłyby się przesunąć. 
                # Tutaj upraszczamy - dla znalezionych wywołań będziemy czyścić ich reprezentację po wszystkim.

        # Oczyszczenie tekstu z zebranych JSONów i niechcianych znaczników.
        for parsed, start_idx, end_idx in reversed(extracted_jsons):
            # Prosty fallback - usuwamy blok JSON z oryginalnego tekstu 
            json_str = response_text[start_idx:end_idx]
            message_content = message_content.replace(json_str, "")

        # Oczyszczenie z resztek markdowna lub śmieciowych znaczników Qwen 2.5
        message_content = message_content.replace("</tool_call>", "").replace("<tool_call>", "").replace("```json", "").replace("```", "").replace("icz", "").strip()
        
        return tool_calls, message_content

    def generate_response(self, prompt: str, tools_registry, status_callback: Any = None, stream_callback: Any = None, final_response_callback: Any = None) -> str:
        """Generuje zapytanie do modelu LLM z użyciem narzędzi i historii.
        
        Implementuje pętlę ReAct (Reasoning and Acting) w jednym przebiegu generowania.
        Narzędzia są zawsze dostępne. Model sam decyduje kiedy ich użyć.
        
        Args:
            prompt (str): Polecenie od użytkownika.
            tools_registry: Instancja rejestru narzędzi.
            status_callback (callable): Funkcja wywoływana z informacją o używanych narzędziach.
            stream_callback (callable): Funkcja wywoływana z każdym nowym tokenem tekstu.
            final_response_callback (callable): Wywoływana dokładnie raz z kompletnym tekstem finalnej
                odpowiedzi agenta (po zakończeniu pętli ReAct). Przeznaczona dla warstwy TTS.
            
        Returns:
            str: Tekstowa odpowiedź od modelu.
        Raises:
            LLMConnectionError: Jeśli wygenerowanie odpowiedzi się nie powiodło.
        """
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

        # Pętla ReAct — kontynuuje dopóki model wywołuje narzędzia.
        # Przy braku wywołań narzędzi model zwraca finalną odpowiedź i pętla się kończy.
        had_tool_calls = False
        while True:
            # Jeśli w poprzedniej iteracji były tool_calls, teraz generujemy finalną odpowiedź.
            is_scratchpad_phase = not had_tool_calls
            payload = {
                "model": self.model_name,
                "messages": messages,
                "tools": tools_registry.tools_schema,
                "stream": True,
                "options": {
                    "temperature": self.temperature,
                    "num_ctx": 4096,
                    "top_p": 0.8,
                    "repeat_penalty": 1.05,
                    "num_predict": 512
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
                        if stream_callback:
                            stream_callback(piece, is_scratchpad_phase)

                    if "tool_calls" in msg_chunk:
                        tool_calls_accumulator.extend(msg_chunk["tool_calls"])

                response_text = full_content

                # Fallback parser — gdy model wypluje JSON w tekście zamiast w tool_calls
                if not tool_calls_accumulator and response_text:
                    valid_tools = [t["function"]["name"] for t in tools_registry.tools_schema]
                    extracted_tool_calls, cleaned_text = self._parse_fallback_tool_calls(response_text, valid_tools, status_callback)
                    if extracted_tool_calls:
                        tool_calls_accumulator = extracted_tool_calls
                        response_text = cleaned_text
                        full_content = cleaned_text

                message = {"role": "assistant", "content": full_content}
                if tool_calls_accumulator:
                    message["tool_calls"] = tool_calls_accumulator
                messages.append(message)

                if tool_calls_accumulator:
                    had_tool_calls = True
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

                        args_str = ", ".join(f"{k}={v}" for k, v in args_dict.items())
                        log_text = f"> Regis używa: {function_name}({args_str})"

                        if status_callback:
                            status_callback(log_text)

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
                    # Brak wywołań narzędzi — to jest finalna odpowiedź modelu.
                    response_text = message.get("content", "")
                    now_assistant = datetime.datetime.now().strftime("%H:%M:%S")
                    self.history.append({"role": "assistant", "content": response_text, "timestamp": now_assistant})

                    if len(self.history) > self.history_limit:
                        self.history = self.history[-self.history_limit:]

                    if final_response_callback:
                        final_response_callback(response_text)

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

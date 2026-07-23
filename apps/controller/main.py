import asyncio
import json
import logging
import threading
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager

from core import config
from integrations.ha_client import HomeAssistantClient
from core.tools_registry import ToolsRegistry
from apps.worker.node import WorkerNode

logging.basicConfig(level=logging.INFO)

# Globalne instancje — inicjalizowane w lifespan
ha_client = None
tools_registry = None
worker_node = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Uruchamia i zatrzymuje usługi Kontrolera."""
    global ha_client, tools_registry, worker_node

    settings = config.load_settings()
    aliases = config.load_aliases()
    virtual_groups = config.load_virtual_groups()

    # Kontroler: inicjalizacja integracji z Home Assistant
    ha_client = HomeAssistantClient(
        url=settings.get("ha_url", "http://192.168.0.50:8123"),
        token=settings.get("ha_token", "TWÓJ_TOKEN_TUTAJ"),
        aliases=aliases,
        virtual_groups=virtual_groups
    )

    # Kontroler: rejestr narzędzi (zna ha_client i aktywny tier)
    active_tier = settings.get("active_tier", "butler")
    tools_registry = ToolsRegistry(ha_client, active_tier)

    # Konfiguracja węzła roboczego na podstawie aktywnego tieru
    tier_config = {
        "butler": {"model": "qwen2.5:1.5b-instruct", "temperature": 0.1, "history_limit": 0},
        "regis":  {"model": "qwen2.5:14b-instruct",  "temperature": 0.1, "history_limit": 10},
        "prime":  {"model": "qwen2.5:32b-instruct",  "temperature": 0.1, "history_limit": 20},
    }
    tier_cfg = tier_config.get(active_tier, tier_config["butler"])

    # Delegacja inferencji do Węzła Roboczego
    # Uwaga architektoniczna: WorkerNode jest tu importowany bezpośrednio.
    # Po wdrożeniu Rejestru Encji stanie się osobnym procesem HTTP,
    # a Kontroler będzie go tylko wykrywać i routować do niego żądania.
    worker_node = WorkerNode(
        model_name=settings.get("selected_model", tier_cfg["model"]),
        tier=active_tier,
        temperature=tier_cfg["temperature"],
        history_limit=tier_cfg.get("history_limit", settings.get("history_limit", 20))
    )

    logging.info(f"Regis Controller uruchomiony. Tier: {active_tier}")
    yield
    logging.info("Regis Controller zatrzymany.")


app = FastAPI(lifespan=lifespan)


class ChatRequest(BaseModel):
    message: str


@app.post("/v1/chat/stream")
async def chat_stream(request: ChatRequest):
    """Przyjmuje wiadomość tekstową, zwraca odpowiedź modelu jako Server-Sent Events."""
    loop = asyncio.get_event_loop()
    q = asyncio.Queue()

    def on_thought_token(chunk):
        loop.call_soon_threadsafe(q.put_nowait, {"type": "thought", "content": chunk})

    def on_content_token(chunk):
        loop.call_soon_threadsafe(q.put_nowait, {"type": "content", "content": chunk})

    def on_tool_call(msg):
        loop.call_soon_threadsafe(q.put_nowait, {"type": "tool", "content": msg})

    def worker():
        try:
            response_text = worker_node.handle_chat(
                request.message,
                tools_registry,
                on_tool_call=on_tool_call,
                on_thought_token=on_thought_token,
                on_content_token=on_content_token
            )
            loop.call_soon_threadsafe(q.put_nowait, {"type": "done", "content": response_text})
        except Exception as e:
            logging.exception("Błąd generacji odpowiedzi")
            loop.call_soon_threadsafe(q.put_nowait, {"type": "error", "content": str(e)})

    thread = threading.Thread(target=worker)
    thread.start()

    async def event_generator():
        while True:
            item = await q.get()
            yield f"data: {json.dumps(item)}\n\n"
            if item["type"] in ("done", "error"):
                break

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/v1/chat/audio_stream")
async def chat_audio_stream(file: UploadFile = File(...)):
    """Przyjmuje plik WAV, przepuszcza przez STT, a transkrypcję przez LLM. Zwraca SSE."""
    audio_bytes = await file.read()

    loop = asyncio.get_event_loop()
    q = asyncio.Queue()

    def on_stt_result(text):
        loop.call_soon_threadsafe(q.put_nowait, {"type": "stt_result", "content": text})

    def on_thought_token(chunk):
        loop.call_soon_threadsafe(q.put_nowait, {"type": "thought", "content": chunk})

    def on_content_token(chunk):
        loop.call_soon_threadsafe(q.put_nowait, {"type": "content", "content": chunk})

    def on_tool_call(msg):
        loop.call_soon_threadsafe(q.put_nowait, {"type": "tool", "content": msg})

    def worker():
        try:
            response_text = worker_node.handle_audio(
                audio_bytes,
                tools_registry,
                on_stt_result=on_stt_result,
                on_tool_call=on_tool_call,
                on_thought_token=on_thought_token,
                on_content_token=on_content_token
            )
            if response_text == "Nie rozpoznano żadnego tekstu ze strumienia audio.":
                loop.call_soon_threadsafe(q.put_nowait, {"type": "error", "content": response_text})
            else:
                loop.call_soon_threadsafe(q.put_nowait, {"type": "done", "content": response_text})
        except Exception as e:
            logging.exception("Błąd generacji odpowiedzi z audio")
            loop.call_soon_threadsafe(q.put_nowait, {"type": "error", "content": str(e)})

    thread = threading.Thread(target=worker)
    thread.start()

    async def event_generator():
        while True:
            item = await q.get()
            yield f"data: {json.dumps(item)}\n\n"
            if item["type"] in ("done", "error"):
                break

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/v1/clear_history")
async def clear_history():
    """Resetuje historię konwersacji aktywnego węzła roboczego."""
    if worker_node:
        worker_node.clear_history()
    return {"status": "ok"}


def start():
    """Entry point dla CLI (regis-controller)."""
    import uvicorn
    uvicorn.run("apps.controller.main:app", host="0.0.0.0", port=8000)

if __name__ == "__main__":
    start()

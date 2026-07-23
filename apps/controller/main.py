import asyncio
import json
import logging
import threading
from contextlib import asynccontextmanager

import requests
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse, Response, StreamingResponse
from pydantic import BaseModel

from core import config
from core.schemas import ToolExecutionRequest, WorkerRegistrationRequest
from integrations.ha_client import HomeAssistantClient
from core.tools_registry import ToolsRegistry

logging.basicConfig(level=logging.INFO)

# ─── Priorytety tierów do wyboru najlepszego węzła ────────────────────────
_TIER_PRIORITY = {"prime": 3, "regis": 2, "butler": 1}

# ─── Globalne instancje — inicjalizowane w lifespan ───────────────────────
ha_client: HomeAssistantClient | None = None
tools_registry: ToolsRegistry | None = None
worker_registry: dict[str, dict] = {}
_settings_cache: dict = {}


def _pick_worker() -> dict | None:
    """Wybiera najlepszy dostępny węzeł roboczy (preferuje wyższy tier)."""
    if not worker_registry:
        return None
    return max(worker_registry.values(), key=lambda w: _TIER_PRIORITY.get(w["tier"], 0))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Uruchamia i zatrzymuje usługi Kontrolera."""
    global ha_client, tools_registry, _settings_cache

    settings = config.load_settings()
    _settings_cache = settings
    aliases = config.load_aliases()
    virtual_groups = config.load_virtual_groups()

    ha_client = HomeAssistantClient(
        url=settings.get("ha_url", "http://192.168.0.50:8123"),
        token=settings.get("ha_token", "TWÓJ_TOKEN_TUTAJ"),
        aliases=aliases,
        virtual_groups=virtual_groups
    )

    active_tier = settings.get("active_tier", "butler")
    tools_registry = ToolsRegistry(ha_client, active_tier)

    logging.info(f"Regis Controller uruchomiony. Tier: {active_tier}")
    yield
    logging.info("Regis Controller zatrzymany.")


app = FastAPI(lifespan=lifespan)


# ─────────────────────────────────────────────────────────────────────────────
#  Rejestr Węzłów Roboczych
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/v1/workers/register")
async def register_worker(request: WorkerRegistrationRequest):
    """Rejestruje Węzeł Roboczy w Kontrolerze. Wywoływane przez Worker przy starcie."""
    worker_registry[request.id] = {
        "id": request.id,
        "host": request.host,
        "port": request.port,
        "model_name": request.model_name,
        "tier": request.tier,
        "base_url": f"http://{request.host}:{request.port}"
    }
    logging.info(f"Zarejestrowano węzeł: {request.id} @ {request.host}:{request.port} (tier={request.tier})")
    return {"status": "registered", "id": request.id}


@app.delete("/v1/workers/{worker_id}")
async def unregister_worker(worker_id: str):
    """Wyrejestrowuje Węzeł Roboczy. Wywoływane przez Worker przy zamknięciu."""
    if worker_id in worker_registry:
        del worker_registry[worker_id]
        logging.info(f"Wyrejestrowano węzeł: {worker_id}")
    return {"status": "ok"}


@app.get("/v1/workers")
async def list_workers():
    """Zwraca listę aktywnych węzłów roboczych (diagnostyka)."""
    return {"workers": list(worker_registry.values())}


# ─────────────────────────────────────────────────────────────────────────────
#  Proxy Narzędzi (Tool Execution)
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/v1/tools/execute")
async def execute_tool_proxy(request: ToolExecutionRequest):
    """Proxy wywołań narzędzi. Węzeł Roboczy nie ma dostępu do HA — wywołuje ten endpoint.

    Kontroler jest jedynym źródłem prawdy dla Home Assistant (MANIFEST.md §3.1).
    Zwraca wynik jako string JSON (identyczny format co ToolsRegistry.execute_tool).
    """
    if not tools_registry:
        return Response(
            json.dumps({"error": "Rejestr narzędzi niedostępny."}, ensure_ascii=False),
            status_code=503,
            media_type="application/json"
        )
    result = tools_registry.execute_tool(request.tool_name, request.arguments)
    return Response(content=result, media_type="application/json")


# ─────────────────────────────────────────────────────────────────────────────
#  Chat (proxy do aktywnego węzła)
# ─────────────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str


def _proxy_sse_to_queue(worker_url: str, payload: dict, q: asyncio.Queue, loop: asyncio.AbstractEventLoop):
    """Pomocnik: odczytuje SSE z Worker i umieszcza eventy w asyncio.Queue."""
    try:
        resp = requests.post(worker_url, json=payload, stream=True, timeout=300)
        resp.raise_for_status()
        for line in resp.iter_lines():
            if not line:
                continue
            line = line.decode("utf-8")
            if line.startswith("data: "):
                try:
                    event = json.loads(line[6:])
                    loop.call_soon_threadsafe(q.put_nowait, event)
                    if event.get("type") in ("done", "error"):
                        break
                except json.JSONDecodeError:
                    pass
    except Exception as e:
        logging.exception("Błąd proxy SSE do węzła")
        loop.call_soon_threadsafe(q.put_nowait, {"type": "error", "content": str(e)})


@app.post("/v1/chat/stream")
async def chat_stream(request: ChatRequest):
    """Przyjmuje wiadomość tekstową — kieruje do aktywnego Węzła Roboczego i proxy-uje SSE."""
    worker = _pick_worker()
    if not worker:
        return JSONResponse(
            {"error": "Brak aktywnych węzłów roboczych. Uruchom regis-worker."},
            status_code=503
        )

    controller_url = _settings_cache.get("controller_url", "http://127.0.0.1:8000")
    worker_url = f"{worker['base_url']}/v1/chat/stream"
    payload = {"message": request.message, "controller_url": controller_url}

    loop = asyncio.get_event_loop()
    q: asyncio.Queue = asyncio.Queue()

    thread = threading.Thread(target=_proxy_sse_to_queue, args=(worker_url, payload, q, loop))
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
    """Przyjmuje plik WAV — kieruje do aktywnego Węzła i proxy-uje SSE."""
    worker = _pick_worker()
    if not worker:
        return JSONResponse(
            {"error": "Brak aktywnych węzłów roboczych. Uruchom regis-worker."},
            status_code=503
        )

    audio_bytes = await file.read()
    controller_url = _settings_cache.get("controller_url", "http://127.0.0.1:8000")
    worker_url = f"{worker['base_url']}/v1/chat/audio_stream"

    loop = asyncio.get_event_loop()
    q: asyncio.Queue = asyncio.Queue()

    def proxy_audio():
        try:
            files = {"file": ("audio.wav", audio_bytes, "audio/wav")}
            data = {"controller_url": controller_url}
            resp = requests.post(worker_url, files=files, data=data, stream=True, timeout=300)
            resp.raise_for_status()
            for line in resp.iter_lines():
                if not line:
                    continue
                line = line.decode("utf-8")
                if line.startswith("data: "):
                    try:
                        event = json.loads(line[6:])
                        loop.call_soon_threadsafe(q.put_nowait, event)
                        if event.get("type") in ("done", "error"):
                            break
                    except json.JSONDecodeError:
                        pass
        except Exception as e:
            logging.exception("Błąd proxy audio do węzła")
            loop.call_soon_threadsafe(q.put_nowait, {"type": "error", "content": str(e)})

    thread = threading.Thread(target=proxy_audio)
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
    """Resetuje historię konwersacji — deleguje do aktywnego węzła."""
    worker = _pick_worker()
    if worker:
        try:
            requests.post(f"{worker['base_url']}/v1/clear_history", timeout=5)
        except requests.RequestException as e:
            logging.warning(f"Nie udało się wyczyścić historii węzła: {e}")
    return {"status": "ok"}


def start():
    """Entry point dla CLI (regis-controller)."""
    import uvicorn
    uvicorn.run("apps.controller.main:app", host="0.0.0.0", port=8000)

if __name__ == "__main__":
    start()

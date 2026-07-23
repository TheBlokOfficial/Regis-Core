import asyncio
import json
import logging
import threading

import requests
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

import regis_controller.registry as registry
from regis_controller.registry import _TIER_PRIORITY

router_chat = APIRouter()

# ─────────────────────────────────────────────────────────────────────────────
#  Chat (proxy do aktywnego węzła)
# ─────────────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    satellite_id: str | None = None


def _proxy_sse_to_queue(payload: dict, q: asyncio.Queue, loop: asyncio.AbstractEventLoop):
    """Pomocnik: odczytuje SSE z Workerów (z Failoverem) i umieszcza eventy w asyncio.Queue."""
    workers = sorted(list(registry.worker_registry.values()), key=lambda w: _TIER_PRIORITY.get(w["tier"], 0), reverse=True)
    if not workers:
        loop.call_soon_threadsafe(q.put_nowait, {"type": "error", "content": "Brak dostępnych węzłów w rejestrze."})
        return

    success = False
    for worker in workers:
        worker_id = worker["id"]
        worker_url = f"{worker['base_url']}/v1/chat/stream"
        logging.info(f"Routowanie żądania do węzła: {worker_id}")
        try:
            resp = requests.post(worker_url, json=payload, stream=True, timeout=(1.0, 300.0))
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
                            success = True
                            break
                    except json.JSONDecodeError:
                        pass
            success = True
            break
        except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError):
            logging.warning(f"Węzeł {worker_id} nie odpowiada (Connect błąd). Usuwam z rejestru.")
            if worker_id in registry.worker_registry:
                del registry.worker_registry[worker_id]
        except Exception as e:
            logging.exception(f"Inny błąd proxy SSE do węzła {worker_id}")
            loop.call_soon_threadsafe(q.put_nowait, {"type": "error", "content": str(e)})
            return

    if not success:
        loop.call_soon_threadsafe(q.put_nowait, {"type": "error", "content": "Wszystkie dostępne węzły zawiodły."})


@router_chat.post("/v1/chat/stream")
async def chat_stream(request: ChatRequest):
    """Przyjmuje wiadomość tekstową — kieruje do aktywnego Węzła Roboczego i proxy-uje SSE."""
    if not registry.worker_registry:
        return JSONResponse(
            {"error": "Błąd Krytyczny: Brak Węzłów. Awaryjny węzeł na Malince (Butler) nie zgłosił gotowości. Sprawdź status regis-worker.service."},
            status_code=503
        )

    controller_url = registry._settings_cache.get("controller_url", "auto")
    if controller_url == "auto":
        from core.discovery import get_local_ip
        controller_url = f"http://{get_local_ip()}:8000"

    # Spatial Context Filtering: wyznaczamy pokój Satelity z rejestru
    room = None
    if request.satellite_id and request.satellite_id in registry.satellite_registry:
        room = registry.satellite_registry[request.satellite_id].get("room")

    payload = {"message": request.message, "controller_url": controller_url, "room": room}

    loop = asyncio.get_event_loop()
    q: asyncio.Queue = asyncio.Queue()

    thread = threading.Thread(target=_proxy_sse_to_queue, args=(payload, q, loop))
    thread.start()

    async def event_generator():
        while True:
            item = await q.get()
            yield f"data: {json.dumps(item)}\n\n"
            if item["type"] in ("done", "error"):
                break

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router_chat.post("/v1/chat/audio_stream")
async def chat_audio_stream(file: UploadFile = File(...)):
    """Przyjmuje plik WAV — kieruje do aktywnego Węzła i proxy-uje SSE."""
    if not registry.worker_registry:
        return JSONResponse(
            {"error": "Błąd Krytyczny: Brak Węzłów. Awaryjny węzeł na Malince (Butler) nie zgłosił gotowości. Sprawdź status regis-worker.service."},
            status_code=503
        )

    audio_bytes = await file.read()
    controller_url = registry._settings_cache.get("controller_url", "auto")
    if controller_url == "auto":
        from core.discovery import get_local_ip
        controller_url = f"http://{get_local_ip()}:8000"

    loop = asyncio.get_event_loop()
    q: asyncio.Queue = asyncio.Queue()

    def proxy_audio():
        workers = sorted(list(registry.worker_registry.values()), key=lambda w: _TIER_PRIORITY.get(w["tier"], 0), reverse=True)
        if not workers:
            loop.call_soon_threadsafe(q.put_nowait, {"type": "error", "content": "Brak dostępnych węzłów w rejestrze."})
            return

        success = False
        for worker in workers:
            worker_id = worker["id"]
            worker_url = f"{worker['base_url']}/v1/chat/audio_stream"
            logging.info(f"Routowanie żądania audio do węzła: {worker_id}")
            try:
                files = {"file": ("audio.wav", audio_bytes, "audio/wav")}
                data = {"controller_url": controller_url}
                resp = requests.post(worker_url, files=files, data=data, stream=True, timeout=(1.0, 300.0))
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
                                success = True
                                break
                        except json.JSONDecodeError:
                            pass
                success = True
                break
            except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError):
                logging.warning(f"Węzeł {worker_id} nie odpowiada (Connect błąd). Usuwam z rejestru.")
                if worker_id in registry.worker_registry:
                    del registry.worker_registry[worker_id]
            except Exception as e:
                logging.exception(f"Inny błąd proxy audio do węzła {worker_id}")
                loop.call_soon_threadsafe(q.put_nowait, {"type": "error", "content": str(e)})
                return
                
        if not success:
            loop.call_soon_threadsafe(q.put_nowait, {"type": "error", "content": "Wszystkie dostępne węzły zawiodły."})

    thread = threading.Thread(target=proxy_audio)
    thread.start()

    async def event_generator():
        while True:
            item = await q.get()
            yield f"data: {json.dumps(item)}\n\n"
            if item["type"] in ("done", "error"):
                break

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router_chat.post("/v1/clear_history")
async def clear_history():
    """Resetuje historię konwersacji — deleguje do aktywnego węzła."""
    worker = registry._pick_worker()
    if worker:
        try:
            requests.post(f"{worker['base_url']}/v1/clear_history", timeout=5)
        except requests.RequestException as e:
            logging.warning(f"Nie udało się wyczyścić historii węzła: {e}")
    return {"status": "ok"}

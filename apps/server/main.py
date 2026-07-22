import asyncio
import json
import logging
import threading
import io
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager

from core import config
from core.llm_engine import LLMEngine
from integrations.ha_client import HomeAssistantClient
from core.tools_registry import ToolsRegistry
from core.stt_engine import STTEngine

logging.basicConfig(level=logging.INFO)

# Globalne instancje
llm_engine = None
ha_client = None
tools_registry = None
stt_engine = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global llm_engine, ha_client, tools_registry, stt_engine
    settings = config.load_settings()
    aliases = config.load_aliases()
    virtual_groups = config.load_virtual_groups()
    
    ha_client = HomeAssistantClient(
        url=settings.get("ha_url", "http://192.168.0.50:8123"),
        token=settings.get("ha_token", "TWÓJ_TOKEN_TUTAJ"),
        aliases=aliases,
        virtual_groups=virtual_groups
    )
    
    active_tier = settings.get("active_tier", "butler")
    tier_config = {
        "butler": {"model": "qwen2.5:1.5b-instruct", "temperature": 0.1, "history_limit": 0},
        "regis": {"model": "qwen2.5:14b-instruct", "temperature": 0.1, "history_limit": 10},
        "prime": {"model": "qwen2.5:32b-instruct", "temperature": 0.1, "history_limit": 20}
    }
    tier_cfg = tier_config.get(active_tier, tier_config["butler"])
    
    llm_engine = LLMEngine(
        model_name=settings.get("selected_model", tier_cfg["model"]),
        tier=active_tier,
        temperature=tier_cfg["temperature"],
        history_limit=tier_cfg.get("history_limit", settings.get("history_limit", 20))
    )
    tools_registry = ToolsRegistry(ha_client, active_tier)
    stt_engine = STTEngine(model_size="small", language="pl")
    
    logging.info(f"Regis Core API Server started. Tier: {active_tier}")
    yield
    logging.info("Regis Core API Server stopped.")

app = FastAPI(lifespan=lifespan)

class ChatRequest(BaseModel):
    message: str

@app.post("/v1/chat/stream")
async def chat_stream(request: ChatRequest):
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
            response_text = llm_engine.generate_response(
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
    audio_bytes = await file.read()
    
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
            audio_io = io.BytesIO(audio_bytes)
            text = stt_engine.transcribe_audio_file(audio_io)
            
            if not text:
                loop.call_soon_threadsafe(q.put_nowait, {"type": "error", "content": "Nie rozpoznano żadnego tekstu ze strumienia audio."})
                return
                
            loop.call_soon_threadsafe(q.put_nowait, {"type": "stt_result", "content": text})
            
            response_text = llm_engine.generate_response(
                text,
                tools_registry,
                on_tool_call=on_tool_call,
                on_thought_token=on_thought_token,
                on_content_token=on_content_token
            )
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
    if llm_engine:
        llm_engine.clear_history()
    return {"status": "ok"}

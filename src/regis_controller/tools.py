import json
from fastapi import APIRouter
from fastapi.responses import Response

from core.schemas import ToolExecutionRequest
import regis_controller.registry as registry

router_tools = APIRouter()

# ─────────────────────────────────────────────────────────────────────────────
#  Proxy Narzędzi (Tool Execution)
# ─────────────────────────────────────────────────────────────────────────────

@router_tools.post("/v1/tools/execute")
async def execute_tool_proxy(request: ToolExecutionRequest):
    """Proxy wywołań narzędzi. Węzeł Roboczy nie ma dostępu do HA — wywołuje ten endpoint.

    Kontroler jest jedynym źródłem prawdy dla Home Assistant (MANIFEST.md §3.1).
    Parametr `room` z requesta jest przekazywany do ToolsRegistry — filtruje urządzenia
    do pokoju Satelity, która zainicjowała żądanie.
    Zwraca wynik jako string JSON (identyczny format co ToolsRegistry.execute_tool).
    """
    if not registry.tools_registry:
        return Response(
            json.dumps({"error": "Rejestr narzędzi niedostępny."}, ensure_ascii=False),
            status_code=503,
            media_type="application/json"
        )
    # Wstrzykujemy room do argumentów — execute_tool odczyta go przez dispatch
    arguments = dict(request.arguments)
    if request.room is not None and "room" not in arguments:
        arguments["room"] = request.room
    result = registry.tools_registry.execute_tool(request.tool_name, arguments)
    return Response(content=result, media_type="application/json")

import asyncio
import json
import time
from typing import Dict, List, Any, Optional

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
import websockets
from websockets import WebSocketClientProtocol

# === CONFIGURATION ===
API_KEY = "REPLACE_ME" # This is an API Key for proxy authentication
WS_URL = "wss://example.com/ws"  # This should be overridden or injected
WS_TIMEOUT = 5  # Timeout in seconds for recv()
RATE_LIMIT = 20
RATE_LIMIT_WINDOW = 60

app = FastAPI()

# === SECURITY / RATE LIMITING ===

api_key_header = APIKeyHeader(name="X-API-Key")
request_history: Dict[str, List[float]] = {}

async def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

async def rate_limit(request: Request):
    client_ip = request.client.host
    now = time.time()
    request_history.setdefault(client_ip, [])
    request_history[client_ip] = [t for t in request_history[client_ip] if now - t < RATE_LIMIT_WINDOW]
    if len(request_history[client_ip]) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    request_history[client_ip].append(now)

# === SESSION STATE ===
session_connections: Dict[str, WebSocketClientProtocol] = {}

# === MODELS ===

class OpenSessionRequest(BaseModel):
    session_id: str
    metadata: Optional[Dict[str, Any]] = None

class MessageRequest(BaseModel):
    session_id: str
    message: str
    metadata: Optional[Dict[str, Any]] = None

class CloseSessionRequest(BaseModel):
    session_id: str

class ProxyResponse(BaseModel):
    session_id: str
    response: str

# ====================================================================================
#                            🔌 CUSTOMIZABLE HOOKS (ENTRYPOINT)
# ====================================================================================

async def on_open_session(ws: WebSocketClientProtocol, session_id: str, metadata: Optional[Dict[str, Any]]):
    """
    Called when a session is opened. You can send multiple auth/init messages here.
    """
    init_payload = {
        "type": "open",
        "session_id": session_id,
        "metadata": metadata or {}
    }
    await ws.send(json.dumps(init_payload))
    # Wait for initial response or handshake if required
    await asyncio.wait_for(ws.recv(), timeout=WS_TIMEOUT)


async def on_send_message(ws: WebSocketClientProtocol, session_id: str, message: Any, metadata: Optional[Dict[str, Any]]):
    """
    Called when a message is being sent. Customize the payload format here.
    """
    message_payload = {
        "type": "message",
        "session_id": session_id,
        "message": message,
        "metadata": metadata or {}
    }
    await ws.send(json.dumps(message_payload))


async def on_receive_response(ws: WebSocketClientProtocol) -> List[Any]:
    """
    Called to receive all chunks of the response. Can be streaming or batched.
    """
    responses = []
    last_message_time = time.time()

    while True:
        try:
            raw = await asyncio.wait_for(ws.recv(), timeout=WS_TIMEOUT)
            parsed = await parse_response(raw)
            responses.append(parsed)
            last_message_time = time.time()
        except asyncio.TimeoutError:
            if time.time() - last_message_time > WS_TIMEOUT:
                break
        except Exception:
            break

    return responses


async def on_close_session(ws: WebSocketClientProtocol, session_id: str):
    """
    Called before closing the session. Send any cleanup messages if necessary.
    """
    # Optional: send session-close notice
    try:
        await ws.send(json.dumps({"type": "close", "session_id": session_id}))
    except Exception:
        pass  # May already be disconnected

    await ws.close()

# ====================================================================================
#                             🔧 UTILITIES
# ====================================================================================

async def parse_response(raw: str) -> Any:
    """
    Parse incoming message from backend WebSocket.
    Override this function to handle different formats.
    """
    try:
        data = json.loads(raw)
        return data.get("response") or data
    except json.JSONDecodeError:
        return raw

# ====================================================================================
#                             🚀 ROUTES
# ====================================================================================

@app.post("/open_session")
async def open_session(req: OpenSessionRequest, request: Request, api_key: str = Depends(verify_api_key)):
    await rate_limit(request)

    if req.session_id in session_connections:
        raise HTTPException(status_code=400, detail="Session already exists")

    try:
        ws = await websockets.connect(WS_URL)
        session_connections[req.session_id] = ws
        await on_open_session(ws, req.session_id, req.metadata)
        return {"status": "session opened", "session_id": req.session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to open session: {str(e)}")


@app.post("/send_message", response_model=ProxyResponse)
async def send_message(req: MessageRequest, request: Request, api_key: str = Depends(verify_api_key)):
    await rate_limit(request)

    ws = session_connections.get(req.session_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        await on_send_message(ws, req.session_id, req.message, req.metadata)
        responses = await on_receive_response(ws)
        return ProxyResponse(session_id=req.session_id, response=responses)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending message: {str(e)}")


@app.post("/close_session")
async def close_session(req: CloseSessionRequest, request: Request, api_key: str = Depends(verify_api_key)):
    await rate_limit(request)

    ws = session_connections.pop(req.session_id, None)
    if not ws:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        await on_close_session(ws, req.session_id)
        return {"status": "session closed", "session_id": req.session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error closing session: {str(e)}")

# ====================================================================================
#                             🧪 LOCAL DEV
# ====================================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("ws:app", host="0.0.0.0", port=8000, reload=True)

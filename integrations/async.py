from fastapi import FastAPI, HTTPException, Request, status, Depends
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from starlette.responses import JSONResponse
from typing import Any
import asyncio
import aiohttp
import os

    
##############################
########### CONFIG ###########
##############################

""" URL of target server """
TARGET_URL = "http://example.com/chat"
""" Endpoint of callback that target server calls (can include parametars defined inside {}) """
CALLBACK_PATH = "/callback/{session_id}"
""" Timeout for waiting for response from target """
RESPONSE_TIMEOUT = 300
""" API Key for the server. 'x-api-key' header must be set to this value. If None, no API key is required. """
API_KEY = None

class ChatRequest(BaseModel):
    """ Request model for chat endpoint. """
    """ Must contain session_id and message. """
    session_id: str
    message: str

class CallbackRequest(BaseModel):
    """ Request model for callback endpoint. """
    message: str

async def send_to_target(data: ChatRequest, is_new_session: bool = False):
    """
    Send the message to the target. This function needs to be implemented to
    integrate with the actual target system, possibly over network calls.
    
    Args:
        data (ChatRequest): The data passed from chat endpoint.
        is_new_session (bool): Whether the session is new or not.

    Raises:
        aiohttp.ClientError: If there is an error during the network call.

    Returns:
        None
    """
    message = data.message

    headers = {
        'Content-Type': 'application/json',
    }

    data = {
        'message': message
    }

    async with aiohttp.ClientSession() as session:
        await session.post(TARGET_URL, headers=headers, json=data)
    

def parse_callback_request(path_variables: dict[str, Any], data: CallbackRequest) -> tuple[str, str]:
    """
    Parses the callback request and extracts the session ID and message.

    Args:
        path_variables (dict[str, Any]): The path variables from the callback request.
        data 

    Returns:
        tuple[str, str]: A tuple containing the session ID and message extracted from the callback request.
    """
    session_id = path_variables['session_id']
    message = data.message

    return session_id, message
    
##############################
############ CODE ############
##############################

# Constants
PORT = os.getenv('PORT', 8000)

app = FastAPI()
api_key_header = APIKeyHeader(name='x-api-key', auto_error=False)

# This dictionary maps session IDs to asyncio queues. Each queue holds responses from the target.
session_responses: dict[str, asyncio.Queue] = {}

@app.post('/chat')
async def chat(request: ChatRequest, api_key: str = Depends(api_key_header)):
    """ Endpoint for the client to initiate or continue a conversation. """

    if API_KEY is not None and api_key != API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")

    session_id = request.session_id
    is_new_session = session_id not in session_responses

    if is_new_session:
        session_responses[session_id] = asyncio.Queue()

    # Forward the message to the target
    await send_to_target(request, is_new_session)

    # Wait for the response from the target with a timeout of RESPONSE_TIMEOUT seconds
    try:
        response_message = await asyncio.wait_for(session_responses[session_id].get(), RESPONSE_TIMEOUT)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="No response from target")

    return {'message': response_message, 'session_id': session_id}
@app.post(CALLBACK_PATH)
async def callback(request: Request):
    """ Endpoint for the target to send back responses. """
    path_variables = request.path_params
    data = await request.json()

    session_id, response_message = parse_callback_request(path_variables, data)
    
    if session_id in session_responses:
        await session_responses[session_id].put(response_message)
        return {'status': 'success'}
    else:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={'error': 'Invalid session ID'})

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=PORT)

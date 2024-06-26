import os
import openai
import uvicorn
from pydantic import BaseModel
from cachetools import TTLCache
from fastapi import FastAPI, Depends
from fastapi.security import APIKeyHeader
from fastapi.responses import JSONResponse

######################
####### CONFIG #######
######################

""" Hugging Face model name. """
HF_MODEL = ""
""" Hugging Face model token. """
HF_TOKEN = ""
""" System prompt for the assistant. """
SYSTEM_PROMPT = "You are helpful assistant."
""" API key for the server authorization. """
API_KEY = None


######################
######## CODE ########
######################

PORT = os.getenv("PORT", 8000)

app = FastAPI()
api_key_header = APIKeyHeader(name='x-api-key', auto_error=False)

cache = TTLCache(maxsize=10000, ttl=300) # 5 minutes
client = openai.AsyncOpenAI(
    base_url=f"https://api-inference.huggingface.co/models/{HF_MODEL}/v1",
    api_key=HF_TOKEN
)

class ChatRequest(BaseModel):
    message: str
    session_id: str

@app.post("/chat")
async def chat(request: ChatRequest, api_key: str = Depends(api_key_header)):
    if API_KEY is not None and api_key != API_KEY:
        return JSONResponse(status_code=401, content={"error": "Unauthorized"})
    
    session_id = request.session_id
    message = request.message

    if session_id not in cache:
        cache[session_id] = [{
            "role": "system",
            "content": SYSTEM_PROMPT
        }]

    cache[session_id].append({
        "role": "user",
        "content": message
    })

    try:
        response = await client.chat.completions.create(
            model=HF_MODEL,
            messages=cache[session_id]
        )

        cache[session_id].append({
            "role": "assistant",
            "content": response.choices[0].message.content
        })

        return JSONResponse(content={"session_id": session_id, "message": response.choices[0].message.content})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
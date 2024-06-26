# Integrations

Collection of template scripts to help you integrate Probe with your Chatbot.

## Standard

Probe requires following endpoints to be implemented in integration scripts to work properly:

- POST /chat
  - Request:
    - session_id: string
    - message: string
  - Response:
    - message: string

## Async

Template script for integration where Chatbot is answering asynchronously with usage of Callback endpoint.

### Configuration

- `TARGET_URL` - URL of Chatbot endpoint
- `CALLBACK_PATH` - Path to Callback endpoint, can contain variables
- `CALLBACK_TIMEOUT` - Timeout for Callback endpoint in seconds
- `API_KEY` - API Key for /chat endpoint

## HuggingFace

Template script for integration with HuggingFace Inference API.

### Configuration

- `HF_MODEL` - Model name from HuggingFace Model Hub
- `HF_TOKEN` - HuggingFace API Token
- `SYSTEM_PROMPT` - System prompt for Chatbot
- `API_KEY` - API Key for /chat endpoint

# GenAI MCP Distributed Project

This project demonstrates a distributed system using the **Model Context Protocol (MCP)**.
It consists of a centrally hosted server exposing GenAI tools and a client that consumes them over the network.

## Architecture
- **Server**: FastAPI application using `mcp.server.sse`. Exposes Weather, Travel, and Memory tools.
- **Client**: Python script using `google-generativeai` and `mcp.client.sse`.

## Setup
1. Copy `.env.example` to `.env` and fill in your API keys.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
### 1. Start the Server
```bash
python -m server.app
```
(Or use `uvicorn server.app:app --reload`)

### 2. Run the Client
```bash
python -m client.client
```

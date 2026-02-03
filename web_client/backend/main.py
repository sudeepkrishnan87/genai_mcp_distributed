import uvicorn
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from web_client.backend.mcp_client import MCPManager
from web_client.backend.history import HistoryManager
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global Managers
mcp_manager = MCPManager()
history_manager = HistoryManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to MCP Server
    logger.info("Attempting to connect to MCP Server...")
    try:
        await mcp_manager.connect()
        logger.info("Successfully connected to MCP Server.")
    except Exception as e:
        logger.error(f"Failed to connect to MCP Server: {e}")
        # We don't raise here to allow the server to start, but requests will fail
    
    yield
    # Shutdown: Disconnect
    logger.info("Disconnecting from MCP Server...")
    await mcp_manager.disconnect()

app = FastAPI(lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For dev only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    tool_calls: List[Dict[str, Any]] = []

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        if not mcp_manager.session:
            logger.warning("MCP Session is None, attempting reconnect...")
            try:
                 await mcp_manager.connect()
            except Exception as reconnect_err:
                 raise HTTPException(status_code=503, detail=f"MCP Server not connected and reconnect failed: {reconnect_err}")
            
        # Get history
        session_id = request.session_id
        if not session_id:
             session_id = history_manager.create_session()
             
        history = history_manager.get_history(session_id)
        
        # Call Gemini via MCP Manager
        result = await mcp_manager.process_message(request.message, history)
        
        # Save interaction
        history_manager.add_message(session_id, "user", request.message)
        history_manager.add_message(session_id, "assistant", result["response"])
        
        return ChatResponse(
            response=result["response"], 
            session_id=session_id, 
            tool_calls=result.get("tool_calls", [])
        )
        
    except Exception as e:
        logger.error(f"Error processing chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/history")
async def get_all_sessions():
    return history_manager.list_sessions()

@app.get("/api/history/{session_id}")
async def get_session_history_endpoint(session_id: str):
    return history_manager.get_history(session_id)

if __name__ == "__main__":
    uvicorn.run("web_client.backend.main:app", host="0.0.0.0", port=8000, reload=True)

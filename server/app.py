import uvicorn
from mcp.server.sse import SseServerTransport
from mcp.server import Server
from mcp.types import Tool, TextContent, EmbeddedResource, ImageContent
import asyncio
from contextlib import asynccontextmanager
from starlette.applications import Starlette
from starlette.routing import Mount, Route

# Import tools
from server.tools.weather import get_weather
from server.tools.travel import search_flights, search_hotels
from server.tools.memory import store_memory, retrieve_memory

# Initialize MCP Server
mcp_server = Server("Distributed GenAI Server")

# -- Register Tools Handlers --

async def handle_list_tools(params):
    return [
        Tool(
            name="get_weather",
            description="Get the current weather for a specific city.",
            inputSchema={
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"]
            }
        ),
        Tool(
            name="search_flights",
            description="Search for flights between two cities.",
            inputSchema={
                "type": "object",
                "properties": {
                    "origin": {"type": "string"},
                    "destination": {"type": "string"},
                    "departure_date": {"type": "string", "description": "YYYY-MM-DD"}
                },
                "required": ["origin", "destination", "departure_date"]
            }
        ),
        Tool(
            name="search_hotels",
            description="Search for hotels in a specific city.",
            inputSchema={
                "type": "object",
                "properties": {"city_code": {"type": "string"}},
                "required": ["city_code"]
            }
        ),
        Tool(
            name="store_memory",
            description="Store a text memory with its vector embedding.",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "vector": {"type": "array", "items": {"type": "number"}}
                },
                "required": ["text", "vector"]
            }
        ),
        Tool(
            name="retrieve_memory",
            description="Retrieve relevant memories based on vector embedding.",
            inputSchema={
                "type": "object",
                "properties": {
                    "vector": {"type": "array", "items": {"type": "number"}},
                    "top_k": {"type": "integer"}
                },
                "required": ["vector"]
            }
        )
    ]

async def handle_call_tool(name, arguments):
    print(f"Executing tool: {name} with args: {arguments}")
    try:
        if name == "get_weather":
            result = get_weather(arguments["city"])
            return [TextContent(type="text", text=result)]
            
        elif name == "search_flights":
            result = search_flights(
                arguments.get("origin"), 
                arguments.get("destination"), 
                arguments.get("departure_date")
            )
            return [TextContent(type="text", text=result)]
            
        elif name == "search_hotels":
            result = search_hotels(arguments["city_code"])
            return [TextContent(type="text", text=result)]
            
        elif name == "store_memory":
            result = store_memory(arguments["text"], arguments["vector"])
            return [TextContent(type="text", text=result)]
            
        elif name == "retrieve_memory":
            top_k = arguments.get("top_k", 3)
            result = retrieve_memory(arguments["vector"], top_k)
            return [TextContent(type="text", text=result)]
            
        return []
    except Exception as e:
        print(f"Error executing tool {name}: {e}")
        return [TextContent(type="text", text=f"Error: {e}")]

# Register handlers to the MCP server instance
mcp_server.list_tools_handler = handle_list_tools
mcp_server.call_tool_handler = handle_call_tool

# -- Starlette App Setup --

sse = SseServerTransport("messages")

async def handle_sse(scope, receive, send):
    """ASGI Handler for SSE connection"""
    async with sse.connect_sse(scope, receive, send) as streams:
        await mcp_server.run(
            streams[0], 
            streams[1], 
            mcp_server.create_initialization_options()
        )

async def handle_messages(scope, receive, send):
    """ASGI Handler for Message POSTs"""
    await sse.handle_post_message(scope, receive, send)

async def dispatcher(scope, receive, send):
    if scope["method"] == "POST":
        print("DEBUG: Dispatching to handle_messages")
        await handle_messages(scope, receive, send)
    else:
        print("DEBUG: Dispatching to handle_sse")
        await handle_sse(scope, receive, send)

app = Starlette(debug=True, routes=[
    Mount("/sse", app=dispatcher),
])

if __name__ == "__main__":
    uvicorn.run("server.app:app", host="0.0.0.0", port=8001, reload=True)

import asyncio
import os
from mcp import ClientSession
from mcp.client.sse import sse_client
from dotenv import load_dotenv

load_dotenv()

# Server URL
SERVER_URL = "http://localhost:8001/sse"

async def test_run():
    print(f"Connecting to {SERVER_URL}...")
    try:
        async with sse_client(SERVER_URL) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                tools = await session.list_tools()
                print(f"Tools found: {[t.name for t in tools.tools]}")
                
                # Test Weather
                print("Testing get_weather...")
                res = await session.call_tool("get_weather", arguments={"city": "Tokyo"})
                print(f"Result: {res.content}")
                
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_run())

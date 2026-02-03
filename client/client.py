import asyncio
import os
import warnings
import google.generativeai as genai
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.sse import sse_client

# Suppress the Google GenAI deprecation warning
warnings.filterwarnings("ignore", category=FutureWarning, module="google.generativeai")
warnings.filterwarnings("ignore", category=UserWarning, module="google.generativeai")

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

# Server URL (SSE Endpoint)
SERVER_URL = "http://localhost:8001/sse"

async def run_client():
    print(f"Connecting to MCP Server at {SERVER_URL}...")
    
    try:
        async with sse_client(SERVER_URL) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize
                await session.initialize()
                
                # List tools
                tools_result = await session.list_tools()
                mcp_tools = tools_result.tools
                print(f"Connected! Found {len(mcp_tools)} tools: {[t.name for t in mcp_tools]}")
                
                # Prepare Gemini Tools
                gemini_tools = []
                for tool in mcp_tools:
                    gemini_tools.append({
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema
                    })
                
                # Initialize Model
                model = genai.GenerativeModel(
                    model_name='gemini-flash-latest',
                    tools=gemini_tools
                )
                
                chat = model.start_chat(enable_automatic_function_calling=True)
                
                print("\n--- Distributed GenAI Client Started ---")
                print("Type 'quit' to exit.")
                
                while True:
                    user_input = input("\nYou: ")
                    if user_input.lower() in ['quit', 'exit']:
                        break
                    
                    # 1. Send message to Gemini
                    # We use manual function calling handling to keep control
                    # (Automatic requires tool functions to be local callables, which we don't have easily mapped)
                    
                    response = await chat.send_message_async(user_input)
                    
                    part = response.candidates[0].content.parts[0]
                    
                    # 2. Handle Tool Calls
                    while part.function_call:
                        fc = part.function_call
                        tool_name = fc.name
                        args = dict(fc.args)
                        
                        print(f"[Gemini requested tool: {tool_name}]")
                        
                        try:
                            # Call remote tool via MCP
                            result = await session.call_tool(tool_name, arguments=args)
                            
                            # Format output
                            tool_output = ""
                            if result.isError:
                                tool_output = f"Error: {result.content}"
                            else:
                                text_content = []
                                for content in result.content:
                                    if content.type == 'text':
                                        text_content.append(content.text)
                                tool_output = "\n".join(text_content)
                            
                            print(f"[Tool Output]: {tool_output[:100]}...")
                            
                            # Send response back to Gemini
                            response = await chat.send_message_async(
                                genai.protos.Content(
                                    parts=[genai.protos.Part(
                                        function_response=genai.protos.FunctionResponse(
                                            name=tool_name,
                                            response={'result': tool_output}
                                        )
                                    )]
                                )
                            )
                            part = response.candidates[0].content.parts[0]
                            
                        except Exception as e:
                            print(f"Error calling tool: {e}")
                            break
                    
                    # 3. Print Final Response
                    print(f"Gemini: {response.text}")
                    
    except Exception as e:
        print(f"\nConnection Error: {e}")
        print("Make sure the server is running on port 8001.")

if __name__ == "__main__":
    asyncio.run(run_client())

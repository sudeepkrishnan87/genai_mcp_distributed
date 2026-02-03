import os
import asyncio
import google.generativeai as genai
from mcp import ClientSession
from mcp.client.sse import sse_client
from dotenv import load_dotenv

load_dotenv()

SERVER_URL = "http://localhost:8001/sse"
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

from contextlib import AsyncExitStack

# ...

class MCPManager:
    def __init__(self):
        self.session = None
        self.exit_stack = None
        self.model = None
        self.chat = None
        self._sse_client = None

    async def connect(self):
        print(f"Connecting to MCP Server at {SERVER_URL}...")
        try:
            self.exit_stack = AsyncExitStack()
            
            # Start SSE Client
            self._sse_client = sse_client(SERVER_URL)
            read, write = await self.exit_stack.enter_async_context(self._sse_client)
            
            # Start Client Session
            self.session = ClientSession(read, write)
            await self.exit_stack.enter_async_context(self.session)
            
            # Initialize
            await self.session.initialize()
            
            # List Tools and Init Gemini
            await self._setup_gemini()
            
            print("Connected to MCP Server and initialized Gemini.")
            
        except Exception as e:
            print(f"Failed to connect to MCP Server: {e}")
            await self.disconnect()
            raise e

    async def disconnect(self):
        print("Disconnecting from MCP Server...")
        if self.session:
            await self.session.__aexit__(None, None, None)
            self.session = None
        
        if self._sse_client:
            await self._sse_client.__aexit__(None, None, None)
            self._sse_client = None

    async def _setup_gemini(self):
        # List tools
        tools_result = await self.session.list_tools()
        mcp_tools = tools_result.tools
        
        gemini_tools = []
        for tool in mcp_tools:
            gemini_tools.append({
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema
            })
            
        self.model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            tools=gemini_tools
        )
        
        # Start a chat session (stateless for the class, but we use it to handle func calling)
        # For a real multi-user web app, we might want to recreate this or manage history differently
        # But for this demo, we can just use a fresh chat or manage history manually.
        # We will create a fresh chat for every request to ensure statelessness regarding the "Client" object,
        # but we will feed in the history.
        pass

    async def process_message(self, user_message: str, history: list):
        # Reconstruct chat history for Gemini
        formatted_history = []
        for msg in history:
            role = "user" if msg["role"] == "user" else "model"
            formatted_history.append({"role": role, "parts": [msg["content"]]})
            
        chat = self.model.start_chat(history=formatted_history, enable_automatic_function_calling=True)
        
        # Standard Gemini Function Calling Loop (Manual)
        # Wait... with enable_automatic_function_calling=True, we need local functions. 
        # But we are calling REMOTE functions via MCP.
        # So we MUST use manual function calling logic, similar to the CLI client.
        
        chat = self.model.start_chat(history=formatted_history) # Disable auto
        
        response = await chat.send_message_async(user_message)
        tool_calls_made = []
        
        # Handle Tool Calls Loop
        while True:
            part = response.candidates[0].content.parts[0]
            
            if not part.function_call:
                break
                
            fc = part.function_call
            tool_name = fc.name
            args = dict(fc.args)
            tool_calls_made.append({"name": tool_name, "args": args})
            
            print(f"[Gemini requested tool: {tool_name}]")
            
            try:
                # Call MCP
                result = await self.session.call_tool(tool_name, arguments=args)
                
                # Format Output
                tool_output = ""
                if result.isError:
                    tool_output = f"Error: {result.content}"
                else:
                    text_content = [c.text for c in result.content if c.type == 'text']
                    tool_output = "\n".join(text_content)
                
                # feedback to Gemini
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
            except Exception as e:
                return {"response": f"Error executing tool: {e}", "tool_calls": tool_calls_made}

        return {"response": response.text, "tool_calls": tool_calls_made}

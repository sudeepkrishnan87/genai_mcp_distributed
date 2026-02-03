import streamlit as st
import asyncio
import os
import warnings
import google.generativeai as genai
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.types import Tool

# Suppress warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="google.generativeai")
warnings.filterwarnings("ignore", category=UserWarning, module="google.generativeai")

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    st.error("GOOGLE_API_KEY not found in environment variables. Please check your .env file.")
    st.stop()

genai.configure(api_key=GOOGLE_API_KEY)

# Constants
SERVER_URL = "http://localhost:8001/sse"

st.set_page_config(page_title="Distributed MCP Viewer", page_icon="🤖", layout="wide")

st.title("🔌 Distributed MCP - Visualizer")
st.markdown("""
This interface demonstrates how the **GenAI Client** (Google Gemini) interacts with the **MCP Server** (Tools) via the **Model Context Protocol**.
""")

# Sidebar for connection status
with st.sidebar:
    st.header("Connection Status")
    status_placeholder = st.empty()
    status_placeholder.info("Connecting to MCP Server...")

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "tools_used" in message:
            for tool_use in message["tools_used"]:
                with st.expander(f"🛠️ Tool Used: `{tool_use['name']}`", expanded=False):
                    st.json(tool_use['args'])
                    st.markdown("**Result:**")
                    st.code(tool_use['result'])

# Chat Input
user_input = st.chat_input("Ask me about weather, flights, or hotels...")

async def run_interaction(user_query):
    try:
        status_placeholder.info(f"Connecting to {SERVER_URL}...")
        
        async with sse_client(SERVER_URL) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # List tools
                tools_result = await session.list_tools()
                mcp_tools = tools_result.tools
                status_placeholder.success(f"Connected! Available Tools: {len(mcp_tools)}")
                
                # Prepare Gemini Tools
                gemini_tools = []
                for tool in mcp_tools:
                    gemini_tools.append({
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema
                    })
                
                model = genai.GenerativeModel(
                    model_name='gemini-flash-latest',
                    tools=gemini_tools
                )
                
                chat = model.start_chat(enable_automatic_function_calling=True)
                
                # 1. Send initial message
                response = await chat.send_message_async(user_query)
                part = response.candidates[0].content.parts[0]
                
                tools_used_log = []
                
                # 2. Handle Tool Calls Loop
                while part.function_call:
                    fc = part.function_call
                    tool_name = fc.name
                    args = dict(fc.args)
                    
                    # Log for UI
                    current_tool_log = {
                        "name": tool_name,
                        "args": args,
                        "result": "Pending..."
                    }
                    
                    try:
                        # Call MCP Tool
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
                        
                        current_tool_log["result"] = tool_output
                        tools_used_log.append(current_tool_log)

                        # Send back to Gemini
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
                        current_tool_log["result"] = f"Error executing tool: {str(e)}"
                        tools_used_log.append(current_tool_log)
                        break

                # 3. Final Response
                return response.text, tools_used_log
                
    except Exception as e:
        return f"Error: {str(e)}", []

if user_input:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Talking to Gemini & MCP Server..."):
            response_text, tools_logs = asyncio.run(run_interaction(user_input))
            
            # Show tools inline for this new message
            if tools_logs:
                for tool_use in tools_logs:
                    with st.expander(f"🛠️ Tool Used: `{tool_use['name']}`", expanded=True):
                        st.json(tool_use['args'])
                        st.markdown("**Result:**")
                        st.code(tool_use['result'])
            
            st.markdown(response_text)
            
            # Save to history
            st.session_state.messages.append({
                "role": "assistant",
                "content": response_text,
                "tools_used": tools_logs
            })

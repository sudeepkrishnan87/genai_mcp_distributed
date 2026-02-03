import os
import google.generativeai as genai
from dotenv import load_dotenv

# Import the actual tool logic from your server code
# This proves the logic is there, we are just bypassing the network layer
from server.tools.weather import get_weather
from server.tools.travel import search_flights, search_hotels
from server.tools.memory import store_memory, retrieve_memory

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# 1. DEFINE TOOLS FOR GEMINI
# In a full MCP setup, the Server sends this schema to the Client.
# Here, we define it manually to show you what the AI sees.
tools_schema = [
    {
        "name": "get_weather",
        "description": "Get the current weather for a specific city.",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"]
        }
    },
    {
        "name": "search_flights",
        "description": "Search for flights between two cities.",
        "parameters": {
            "type": "object",
            "properties": {
                "origin": {"type": "string"},
                "destination": {"type": "string"},
                "departure_date": {"type": "string", "description": "YYYY-MM-DD"}
            },
            "required": ["origin", "destination", "departure_date"]
        }
    }
]

# 2. MAP TOOLS TO FUNCTIONS
# The MCP Server usually does this mapping.
available_functions = {
    "get_weather": get_weather,
    "search_flights": search_flights,
    "search_hotels": search_hotels,
    "store_memory": store_memory,
    "retrieve_memory": retrieve_memory
}

def run_conversation():
    # Pass the actual functions; SDK generates schema automatically
    model = genai.GenerativeModel(model_name='gemini-flash-latest', tools=list(available_functions.values()))
    chat = model.start_chat(enable_automatic_function_calling=True)

    print("\n" + "="*50)
    print("🤖 SIMPLIFIED MCP DEMO")
    print("This script runs the logic locally to explain the flow.")
    print("="*50 + "\n")

    while True:
        user_input = input("You (type 'quit' to exit): ")
        if user_input.lower() in ['quit', 'exit']:
            break

        print(f"\n[Sending to Gemini]: {user_input}")
        
        # In 'enable_automatic_function_calling=True' mode, the library handles the
        # loop of: Model asks for tool -> Code runs tool -> Result sent back -> Model answers.
        # We will use the manual way to show you what happens under the hood.
        
        # MANUAL LOOP FOR EDUCATIONAL PURPOSES
        # We create a new model instance without auto-calling to verify steps
        # We pass the functions, but we will handle the execution manually below
        step_model = genai.GenerativeModel(model_name='gemini-flash-latest', tools=list(available_functions.values()))
        
        try:
            # Step 1: User -> Model
            response = step_model.generate_content(user_input)
            candidate = response.candidates[0]
            
            # Step 2: Does Model want a tool?
            for part in candidate.content.parts:
                if part.function_call:
                    fc = part.function_call
                    print(f"\n[⚡ Gemini Decision]: I need to use a tool!")
                    print(f"  > Tool Name: {fc.name}")
                    print(f"  > Arguments: {fc.args}")
                    
                    # Step 3: Execute Tool (The "MCP Server" part)
                    if fc.name in available_functions:
                        print(f"\n[⚙️ MCP Server]: Running {fc.name}...")
                        func = available_functions[fc.name]
                        # Convert args to dict
                        kwargs = dict(fc.args)
                        
                        try:
                            result = func(**kwargs)
                            print(f"  > Result: {result}")
                            
                            # Step 4: Result -> Model
                            # (For this simple demo, we just print the result. 
                            # To continue the convo, we'd feed this back. 
                            # Let's verify 'automatic' mode does this for us below.)
                        except Exception as e:
                            print(f"  > Error: {e}")
            
            # Now run the full automatic chat to get the final answer text
            final_response = chat.send_message(user_input)
            print(f"\n[💬 Gemini Final Answer]: {final_response.text}")
            
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    run_conversation()

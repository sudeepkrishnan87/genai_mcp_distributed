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

## 🚀 Demo
To understand how the tools work without running the full server-client setup, you can run the standalone demo script:

```bash
python demo_flow.py
```

### Example Console Output
Here is what an interaction looks like when running the demo:

```text
==================================================
🤖 SIMPLIFIED MCP DEMO
This script runs the logic locally to explain the flow.
==================================================

You (type 'quit' to exit): What is the weather in Tokyo?

[Sending to Gemini]: What is the weather in Tokyo?

[⚡ Gemini Decision]: I need to use a tool!
  > Tool Name: get_weather
  > Arguments: {'city': 'Tokyo'}

[⚙️ MCP Server]: Running get_weather...
  > Result: Weather in Tokyo: broken clouds, Temperature: 3.82°C, Humidity: 52%


[💬 Gemini Final Answer]: The weather in Tokyo is broken clouds with a temperature of 3.82°C and 52% humidity.

You (type 'quit' to exit): Find me flights from PAR to LON for 2024-12-25

[Sending to Gemini]: Find me flights from PAR to LON for 2024-12-25

[⚡ Gemini Decision]: I need to use a tool!
  > Tool Name: search_flights
  > Arguments: {'origin': 'PAR', 'destination': 'LON', 'departure_date': '2024-12-25'}

[⚙️ MCP Server]: Running search_flights...
  > Result: Flight: BA304 -> BA305, Price: 156.90 EUR
  > Result: Flight: AF123, Price: 145.50 EUR

[💬 Gemini Final Answer]: I found a few flights for you from Paris (PAR) to London (LON) on December 25th, 2024. The best options are a British Airways flight for €156.90 and an Air France flight for €145.50.
```

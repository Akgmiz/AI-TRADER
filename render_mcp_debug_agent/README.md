# Render MCP Debug Agent

This lightweight Flask service connects to Render's API to fetch build logs and provides a `/debug` endpoint that performs heuristic analysis of build failures. It is intended as a simple Model Control Plane (MCP) helper you can deploy on Render and connect to AI tools (e.g., Claude Code, Cursor) to perform natural-language diagnostics.

## Files
- `render_mcp_server.py` - main Flask app
- `requirements.txt` - Python deps
- `Procfile` - instructions for Render
- `.env.example` - example environment variables

## Deploy on Render (quick)
1. Create a new GitHub repository and add these files.
2. On Render, create a new **Web Service** and connect the repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: `python render_mcp_server.py`
5. Add environment variables in Render dashboard (RENDER_API_TOKEN and RENDER_SERVICE_ID).

## Usage
- `GET /logs` - fetch build logs from Render (requires env vars set)
- `POST /debug` - send JSON `{"logs":"<paste logs here>"}` or omit `logs` to fetch automatically. Returns diagnostic suggestions.
- `GET /health` and `/ready` - basic probes

## Integration with AI tools
- Provide the `/debug` endpoint to your AI assistant or tool. The assistant can POST build logs and receive suggested fixes in natural language.
- For deeper LLM-powered analysis, forward the returned logs to a hosted LLM or Claude/OpenAI API for contextual explanation.



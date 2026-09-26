# AGI Agent by Nexora — Base44 Dev Notes

## What this is
A CLI-based Python AGI agent (ReAct loop) with LLM provider fallback (Gemini → Groq → Ollama) and tools (calculator, web/Youtube search, file system, Python runner, memory). Originally a pure CLI app using `input()`.

## What was added for the preview
- `AGI_Project/web_app.py` — Flask web wrapper (port 3000) that exposes the agent loop via `/api/chat`
- `AGI_Project/templates/index.html` — chat UI
- `AGI_Project/core/brain.py` — **reconstructed from bytecode** (`__pycache__/brain.cpython-314.pyc`); the original `.py` source was missing from the repo

## How to run
```
docker compose -f docker-compose.base44.yml up -d
```
The container installs deps from `AGI_Project/requirements.txt` then starts `python web_app.py` on port 3000.

## Secrets
- `GEMINI_API_KEY` — required for the default provider (Google AI Studio)
- `GROQ_API_KEY` — optional fallback (Groq Console)
- Without either key the app boots and shows the UI, but the agent returns "All providers failed"

## Quirks
- `core/brain.py` was only available as a `.pyc` compiled with Python 3.14; the Docker image uses Python 3.12 and the reconstructed source
- chromadb (semantic memory) and sqlite (episodic memory) store data under `AGI_Project/data/`
- The agent uses a ReAct loop: LLM outputs JSON `{"tool": "...", "query": "..."}`, tools execute, results feed back

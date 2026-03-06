# 🤖 local-agent-stack

> A production-style multi-agent AI system with memory, tools, planning & reflection — running 100% locally via Docker. No cloud APIs. No API keys. Just your machine.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react)](https://react.dev)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)](https://docker.com)
[![Ollama](https://img.shields.io/badge/LLM-Ollama%20llama3-black?logo=ollama)](https://ollama.com)

---

## ✨ What is this?

**local-agent-stack** is a fully working AI agent framework you can run on your own machine. It's built the way real agent systems are built — not a single chatbot script, but a proper multi-agent pipeline with:

- 🧠 **5 specialised agents** working in a coordinated loop
- 🗃️ **3-layer memory** (session history, semantic search, structured profile)
- 🔧 **4 tools** (web search, calculator, job search, file reader)
- 🔄 **Automatic reflection** — the system learns about you over time
- 🖥️ **Clean chat UI** built with React + Vite
- 🐳 **One command to run** with Docker Compose

---

## 📸 Preview

```
┌─────────────────────────────────────────────────┐
│  🤖 AI Agent                                    │
│  Memory · Tools · Planning · Reflection         │
├─────────────────────────────────────────────────┤
│                                                 │
│  🧑  Find backend jobs in Berlin                │
│                                                 │
│  🤖  Based on what I know about you, here are  │
│      5 backend engineering roles in Berlin…     │
│                                                 │
│  🧑  What is 1024 * 365?                        │
│                                                 │
│  🤖  1024 × 365 = 373,760                       │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## 🏗️ Architecture

```
                        ┌──────────────┐
                        │  React UI    │  :5173
                        │  (Vite)      │
                        └──────┬───────┘
                               │ HTTP
                        ┌──────▼───────┐
                        │  FastAPI     │  :8000
                        │  Backend     │
                        └──────┬───────┘
                               │
                    ┌──────────▼──────────┐
                    │  Agent Orchestrator  │
                    └──────────┬──────────┘
                               │
          ┌────────────────────┼─────────────────────┐
          │                    │                     │
   ┌──────▼──────┐    ┌────────▼────────┐   ┌───────▼──────┐
   │   Planner   │    │  Memory Agent   │   │ Tool Agent   │
   │   Agent     │    │  (retrieval)    │   │ (execution)  │
   └──────┬──────┘    └────────┬────────┘   └───────┬──────┘
          │                    │                     │
   ┌──────▼──────┐    ┌────────▼────────┐   ┌───────▼──────┐
   │  Response   │    │   Reflection    │   │    Tools     │
   │   Agent     │    │    Agent        │   │ calc/search  │
   └─────────────┘    └─────────────────┘   └─────────────┘

Memory Layer:
  ┌─────────────┐   ┌─────────────────┐   ┌──────────────┐
  │    Redis    │   │     Qdrant      │   │   MongoDB    │
  │  session    │   │  vector memory  │   │  user profile│
  │  history    │   │  (embeddings)   │   │  (structured)│
  └─────────────┘   └─────────────────┘   └──────────────┘

LLM: Ollama (llama3) running locally at :11434
```

### Agent Pipeline (per message)

```
User message
    │
    ▼
[1] Retrieve Memory      ← Qdrant semantic search + MongoDB profile
    │
    ▼
[2] Plan                 ← Classify: ANSWER | SEARCH | CALC | JOBS | FILE
    │
    ▼
[3] Execute Tool         ← Only if plan requires a tool
    │
    ▼
[4] Generate Response    ← Ollama LLM with memory + tool output injected
    │
    ▼
[5] Store to Redis       ← Append to session history
    │
    ▼
[6] Reflect (background) ← Extract user facts → Qdrant + MongoDB
```

---

## 🚀 Quick Start

### Prerequisites

| Requirement | Version |
|-------------|---------|
| Docker      | ≥ 24    |
| Docker Compose | ≥ 2.20 |
| RAM         | ≥ 8 GB  |
| Disk        | ≥ 10 GB |

### 1. Clone

```bash
git clone https://github.com/YOUR_USERNAME/local-agent-stack.git
cd local-agent-stack
```

### 2. Pull the LLM (one-time setup)

```bash
# Start Ollama container
docker compose up -d ollama

# Wait ~10 seconds, then pull llama3 (~4.7 GB)
docker exec agent-ollama ollama pull llama3
```

> ⚠️ This is a one-time download. The model is cached in a Docker volume.

### 3. Start everything

```bash
docker compose up --build
```

### 4. Open the app

```
http://localhost:5173
```

That's it. 🎉

---

## 💬 Example Conversations

**Calculator**
```
You:    What is 2 to the power of 16?
Agent:  2^16 = 65,536
```

**Web Search**
```
You:    Search for the latest news about Rust programming
Agent:  [Searches DuckDuckGo and summarises results]
```

**Job Search**
```
You:    I'm a backend developer living in Berlin, find me some jobs
Agent:  [Returns job listings, stores your location & preferences in memory]

You:    Find me more jobs     ← (no need to repeat your details)
Agent:  [Automatically uses Berlin + backend from memory]
```

**Memory in action**
```
You:    What do you remember about me?
Agent:  Based on our conversations, I know that you live in Berlin,
        you're a backend developer, and you prefer Python roles…
```

---

## 📁 Project Structure

```
local-agent-stack/
│
├── backend/
│   ├── agents/
│   │   ├── planner_agent.py       # Intent classification → action plan
│   │   ├── tool_agent.py          # Tool dispatch
│   │   ├── memory_agent.py        # Memory retrieval (Qdrant + Mongo)
│   │   ├── reflection_agent.py    # Post-reply fact extraction
│   │   └── response_agent.py      # Final LLM response generation
│   │
│   ├── memory/
│   │   ├── short_memory.py        # Redis session history
│   │   ├── vector_memory.py       # Qdrant semantic memory
│   │   └── profile_memory.py      # MongoDB structured user profile
│   │
│   ├── tools/
│   │   ├── calculator.py          # Safe AST-based arithmetic
│   │   ├── web_search.py          # DuckDuckGo (mock fallback)
│   │   ├── job_search.py          # Job listings (mock / plug in real API)
│   │   └── file_reader.py         # Sandboxed file reading
│   │
│   ├── orchestrator/
│   │   └── agent_loop.py          # Full pipeline orchestration
│   │
│   ├── llm/
│   │   └── ollama_client.py       # Async Ollama API wrapper
│   │
│   ├── api/
│   │   └── chat.py                # FastAPI routes
│   │
│   ├── main.py                    # App bootstrap & CORS
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   └── chat-ui/
│       ├── src/
│       │   ├── App.jsx            # Main chat component
│       │   ├── App.css
│       │   ├── api/
│       │   │   └── client.js      # Axios API wrapper
│       │   └── components/
│       │       ├── MessageBubble.jsx
│       │       ├── Sidebar.jsx     # Profile viewer + quick prompts
│       │       └── TypingIndicator.jsx
│       ├── index.html
│       ├── vite.config.js
│       ├── package.json
│       └── Dockerfile
│
├── docker-compose.yml
└── README.md
```

---

## 🔌 API Reference

### `POST /api/chat`
```json
// Request
{
  "session": "my-session-123",
  "message": "Find backend jobs in Berlin"
}

// Response
{
  "response": "Here are some backend engineering roles in Berlin...",
  "session": "my-session-123"
}
```

### `GET /api/chat/history/{session_id}`
Returns the full conversation history for a session.

### `DELETE /api/chat/history/{session_id}`
Clears the session history (New Chat).

### `GET /api/profile/{session_id}`
Returns the structured user profile extracted by the Reflection Agent.

**Swagger UI:** `http://localhost:8000/docs`

---

## 🔧 Available Tools

| Tool | Triggered when you say… | Notes |
|------|--------------------------|-------|
| 🧮 Calculator | "what is 15 * 7", "calculate 2^10" | Safe AST eval, no `exec()` |
| 🌐 Web Search | "search for...", "latest news about..." | DuckDuckGo API, mock fallback |
| 💼 Job Search | "find jobs", "backend roles in Berlin" | Mock data — plug in Adzuna/LinkedIn |
| 📄 File Reader | "read file report.csv" | Sandboxed to `/tmp/agent_files` |

---

## 🧠 Memory System

### Short-term (Redis)
- Last 40 messages per session
- 24-hour TTL
- Stored as JSON array under `chat:<session_id>`

### Long-term Vector (Qdrant)
- Facts extracted after every reply
- Embedded with `sentence-transformers/all-MiniLM-L6-v2` (384 dims)
- Retrieved via cosine similarity at each new turn
- Example: *"User lives in Berlin and prefers backend engineering"*

### Structured Profile (MongoDB)
- Updated by the Reflection Agent
- Schema: `{ name, location, skills[], preferences{}, facts[] }`
- Automatically used in job search (e.g. injects user's city)

---

## ⚙️ Configuration

Edit environment variables in `docker-compose.yml`:

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_MODEL` | `llama3` | Ollama model name |
| `SESSION_TTL_SECONDS` | `86400` | Redis TTL (24h) |
| `MAX_HISTORY_MESSAGES` | `40` | Max messages in context window |
| `FILE_READER_DIR` | `/tmp/agent_files` | Allowed path for file tool |

### Swap the LLM

```bash
# Edit docker-compose.yml
OLLAMA_MODEL=mistral

# Pull the model
docker exec agent-ollama ollama pull mistral

# Restart
docker compose restart backend
```

---

## 🛠️ Extending the System

### Add a new tool

1. Create `backend/tools/my_tool.py`:
```python
async def my_tool(query: str) -> str:
    return f"Result for {query}"
```

2. Dispatch it in `backend/agents/tool_agent.py`:
```python
if action == "MYTOOL":
    return await my_tool(query)
```

3. Add a rule to the planner system prompt in `backend/agents/planner_agent.py`:
```
MYTOOL – when the user asks about X
```

### Add a real job search API

Replace the mock in `backend/tools/job_search.py` with an HTTP call to [Adzuna](https://developer.adzuna.com/), [Greenhouse](https://developers.greenhouse.io/), or the LinkedIn API.

### Mount files for the file reader

```yaml
# docker-compose.yml
backend:
  volumes:
    - ./my_files:/tmp/agent_files
```

---

## 🐛 Troubleshooting

**`[Error: LLM service unavailable]`**
```bash
# Check if llama3 is pulled
docker exec agent-ollama ollama list
# If empty:
docker exec agent-ollama ollama pull llama3
```

**Backend crashes on startup**
```bash
# Services may still be initialising — check logs
docker compose logs backend --tail=50
# Usually resolves itself within 30 seconds
```

**Slow first response**
> The `sentence-transformers` model downloads on first startup. Subsequent requests are fast. Normal on cold start.

**Frontend can't reach backend**
```bash
# Check VITE_API_URL in docker-compose.yml
# Default: http://localhost:8000
```

---

## 🗺️ Roadmap

- [ ] Streaming responses (SSE / WebSocket)
- [ ] File upload via drag-and-drop
- [ ] Multiple user profiles / auth
- [ ] Real job search API integration
- [ ] Plugin system for custom tools
- [ ] Web UI for browsing vector memories
- [ ] Support for vision models (llava)

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repo
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Commit with conventional commits: `feat:`, `fix:`, `docs:`
4. Open a Pull Request

---

## 📄 License

[MIT](LICENSE) — use it, modify it, build on it.

---

## 🙏 Built with

- [FastAPI](https://fastapi.tiangolo.com/) — async Python web framework
- [Ollama](https://ollama.com/) — local LLM runtime
- [Qdrant](https://qdrant.tech/) — vector similarity search
- [sentence-transformers](https://www.sbert.net/) — semantic embeddings
- [React](https://react.dev/) + [Vite](https://vitejs.dev/) — frontend
- [Redis](https://redis.io/) — in-memory session store
- [MongoDB](https://www.mongodb.com/) — structured data store

---

<p align="center">
  Built with ❤️ · Star ⭐ if this helped you
</p>

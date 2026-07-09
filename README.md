# AI-First CRM HCP Module — Log Interaction Screen

An AI-powered CRM system for Healthcare Professional (HCP) interactions with a **LangGraph agent** that auto-extracts and logs data from natural language chat.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     React + Redux Frontend                    │
│  ┌──────────────────────┐        ┌──────────────────────┐   │
│  │   Interaction Form   │        │   AI Chat Assistant  │   │
│  │   (Auto-populated)   │◄───────│   (Natural Language) │   │
│  └──────────────────────┘        └──────────┬───────────┘   │
└─────────────────────────────────────────────┼───────────────┘
                                               │
                                               ▼
┌──────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                           │
│  ┌──────────────────────────────────────────────────────┐    │
│  │              LangGraph Agent (LLM)                   │    │
│  │  ┌──────────┐ ┌──────────┐ ┌────────┐ ┌─────────┐  │    │
│  │  │   Log    │ │   Edit   │ │ Search │ │ History │  │    │
│  │  │  Tool    │ │  Tool    │ │  HCP   │ │  Tool   │  │    │
│  │  └──────────┘ └──────────┘ └────────┘ └─────────┘  │    │
│  │  ┌──────────┐                                       │    │
│  │  │ Follow-up│                                       │    │
│  │  │  Tool    │                                       │    │
│  │  └──────────┘                                       │    │
│  └──────────────────────────────────────────────────────┘    │
└───────────────────────────────┬──────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────┐
│                    SQLite Database                            │
│                  (hcp_interactions)                           │
└──────────────────────────────────────────────────────────────┘
```

## Features

### LangGraph AI Agent (5 Tools)
| # | Tool | Description |
|---|------|-------------|
| 1 | **Log Interaction** | Extracts HCP name, topics, sentiment, materials, etc. from chat and saves to DB |
| 2 | **Edit Interaction** | Updates any field of an existing interaction |
| 3 | **Search HCP** | Finds all interactions for a given doctor name |
| 4 | **Get Interaction History** | Retrieves full details of a specific interaction |
| 5 | **Create Follow-up** | Adds a follow-up action note to an interaction |

### Frontend
- Split-panel: form on left, AI chat on right
- Form auto-populates from chat via Redux state
- Toast notifications, Save button, field mapping

### Backend
- FastAPI server with LangGraph agent loop
- **NVIDIA NIM** as primary LLM provider — very high rate limits and generous free tier, no daily token caps
- **Groq API** and **Gemini** as fallback providers (tested, code supports seamless switching)
- SQLite database (swap to PostgreSQL via DATABASE_URL)

## Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | React 18, Redux Toolkit, Vite |
| Backend | Python 3, FastAPI, LangGraph, LangChain |
| LLM | **NVIDIA NIM** (meta/llama-3.1-8b-instruct) — primary |
| Fallback LLMs | Groq API (llama-3.3-70b-versatile), Gemini 2.0 Flash |
| Database | SQLite (dev) / PostgreSQL (prod) |
| UI | Custom CSS, Google Inter font |

> **Why NVIDIA NIM?** Groq has daily token caps (100K TPD) and Gemini has per-minute rate limits (5 req/min). NVIDIA NIM offers significantly higher RPM and a very generous free tier, making it ideal for development without hitting rate limits.

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.9+
- NVIDIA API key, Groq API key, or Gemini API key (see `.env.example`)

### Backend
```bash
cd backend
pip install -r requirements.txt
copy .env.example .env   # Add your API key
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## Usage

Type natural language in the chat panel:

| Action | Example |
|--------|---------|
| Log interaction | "Met Dr. Smith about Product X. Positive, shared brochure." |
| Edit interaction | "Actually change sentiment to Neutral for interaction 1" |
| Search HCP | "Search for Dr. Smith" |
| Get history | "Show me interaction 1" |
| Add follow-up | "Add a follow-up for interaction 1: Call next week" |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat` | Send message to AI agent |
| GET | `/api/interactions` | List all interactions |
| GET | `/api/interactions/{id}` | Get one interaction |
| GET | `/api/search/{name}` | Search by HCP name |

## Project Structure

```
backend/
├── app/
│   ├── agent/langgraph_agent.py   # LangGraph agent + LLM loop
│   ├── models/database.py         # SQLAlchemy models
│   ├── models/schemas.py          # Pydantic schemas
│   ├── routes/interactions.py     # API routes
│   ├── tools/hcp_tools.py         # 5 LangGraph tools
│   └── main.py                    # FastAPI entry point
├── requirements.txt
└── .env
frontend/
├── src/
│   ├── components/
│   │   ├── ChatInterface.jsx      # Chat panel
│   │   ├── InteractionForm.jsx    # Form panel
│   │   └── Toast.jsx              # Notifications
│   ├── store/
│   │   ├── store.js               # Redux store
│   │   └── crmSlice.js           # State + field mapping
│   ├── services/api.js            # API client
│   ├── App.jsx
│   └── App.css
└── package.json
```

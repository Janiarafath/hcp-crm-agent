# AI-First CRM HCP Module - Log Interaction Screen

An AI-powered Customer Relationship Management system for Healthcare Professional (HCP) interactions, featuring a LangGraph agent that automatically extracts and logs interaction data from natural language.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      React Frontend                        │
│  ┌─────────────────┐              ┌─────────────────┐     │
│  │  Interaction    │              │  Chat Interface │     │
│  │  Form           │◄─────────────│  (AI Assistant) │     │
│  │  (Auto-filled)  │              │                 │     │
│  └─────────────────┘              └────────┬────────┘     │
└───────────────────────────────────────────┼───────────────┘
                                            │
                                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              LangGraph Agent                        │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  │   │
│  │  │  Log    │ │  Edit   │ │ Search  │ │ Follow  │  │   │
│  │  │  Tool   │ │  Tool   │ │  HCP    │ │  Up     │  │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘  │   │
│  │  ┌─────────────────┐                               │   │
│  │  │ Get History     │                               │   │
│  │  └─────────────────┘                               │   │
│  └─────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────┬───────────────┘
                                            │
                                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    PostgreSQL Database                      │
│                    (hcp_interactions)                       │
└─────────────────────────────────────────────────────────────┘
```

## Features

### Core Functionality
- **Natural Language Input**: Users describe interactions in plain English
- **Auto-populated Form**: AI extracts and fills 12+ fields automatically
- **Real-time Processing**: Instant response with structured data extraction
- **Persistent Storage**: All interactions saved to PostgreSQL database

### LangGraph AI Agent Tools

1. **Log Interaction Tool**: Captures and saves new HCP interactions
2. **Edit Interaction Tool**: Modifies existing interaction records
3. **Search HCP Tool**: Finds interactions by doctor name
4. **Get Interaction History Tool**: Retrieves full details of specific interactions
5. **Create Follow-up Tool**: Adds follow-up actions to interactions

### Frontend
- Split-panel design (form on left, chat on right)
- Redux state management
- Responsive design with Inter font
- Real-time form updates from AI responses

## Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | React 18, Redux Toolkit |
| Backend | Python, FastAPI |
| AI Agent | LangGraph |
| LLM | Groq (gemma2-9b-it) |
| Database | PostgreSQL |
| Styling | Custom CSS with Inter font |

## Prerequisites

- Node.js 18+ and npm
- Python 3.9+
- PostgreSQL database
- Groq API key (get from https://console.groq.com)

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/hcp-crm.git
cd hcp-crm
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with your credentials
cp .env.example .env
# Edit .env with your GROQ_API_KEY and DATABASE_URL
```

### 3. Database Setup

```bash
# Create PostgreSQL database
psql -U postgres -c "CREATE DATABASE hcp_crm;"
```

### 4. Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install
```

## Running the Application

### Start Backend

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Start Frontend

```bash
cd frontend
npm run dev
```

The application will be available at:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Usage

1. Open the application in your browser
2. In the right panel (AI Assistant), describe your HCP interaction:
   ```
   Met Dr. Smith today and discussed Product X efficacy. The meeting was positive, 
   I shared the brochure and clinical data. He seemed interested and wants to see 
   more data next month.
   ```
3. Click "Log" or press Enter
4. The AI will process your message and auto-populate the form on the left
5. Review and manually adjust any fields if needed
6. The interaction is automatically saved to the database

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat` | Send message to AI agent |
| GET | `/api/interactions` | Get all interactions |
| POST | `/api/interactions` | Create new interaction |
| PUT | `/api/interactions/{id}` | Update interaction |
| DELETE | `/api/interactions/{id}` | Delete interaction |
| GET | `/api/search/{name}` | Search HCP by name |

## Project Structure

```
hcp-crm/
├── backend/
│   ├── app/
│   │   ├── agent/
│   │   │   └── langgraph_agent.py    # LangGraph agent setup
│   │   ├── models/
│   │   │   ├── database.py           # SQLAlchemy models
│   │   │   └── schemas.py           # Pydantic schemas
│   │   ├── routes/
│   │   │   └── interactions.py      # API routes
│   │   ├── tools/
│   │   │   └── hcp_tools.py         # 5 LangGraph tools
│   │   └── main.py                  # FastAPI app
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatInterface.jsx    # AI chat component
│   │   │   └── InteractionForm.jsx  # Auto-filled form
│   │   ├── store/
│   │   │   ├── store.js            # Redux store
│   │   │   └── crmSlice.js        # Redux slice
│   │   ├── services/
│   │   │   └── api.js             # API client
│   │   ├── App.jsx
│   │   └── App.css
│   └── package.json
└── README.md
```

## Environment Variables

### Backend (.env)

```env
GROQ_API_KEY=your_groq_api_key_here
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/hcp_crm
```

## Troubleshooting

### Database Connection Issues

Ensure PostgreSQL is running and the database exists:
```bash
psql -U postgres -c "\l"  # List databases
```

### Port Already in Use

```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn app.main:app --port 8001
```

### Groq API Errors

Verify your API key is valid at https://console.groq.com/keys

## License

MIT License

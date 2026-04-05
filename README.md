# 🎓 AI Leadership Tutor

An AI-powered voice tutoring application that teaches leadership skills through interactive spoken conversations. The tutor guides learners through a structured curriculum, asks thought-provoking questions, listens to responses via speech recognition, and provides personalized feedback — all through natural voice interaction.

## Overview

AI Leadership Tutor pairs a curriculum-driven state machine with an LLM (Google Gemini via OpenRouter) and Sarvam AI's speech services to create a conversational learning experience. The tutor speaks aloud, the learner responds with their microphone, and the system transcribes, evaluates, and advances through the lesson automatically.

The app supports **English** and **Hindi**, with voice synthesis and recognition in both languages.

## Architecture

```
┌──────────────────────────────┐
│        React Frontend        │
│  (Vite + Chakra UI + WebSocket)  │
└──────────────┬───────────────┘
               │ WebSocket (voice + control)
               │ REST API (sessions, modules)
┌──────────────▼───────────────┐
│       FastAPI Backend        │
│                              │
│  ┌─────────┐  ┌───────────┐  │
│  │  Tutor  │  │  Routers  │  │
│  │ Engine  │  │ (REST+WS) │  │
│  └────┬────┘  └───────────┘  │
│       │                      │
│  ┌────▼──────────────────┐   │
│  │     Services Layer    │   │
│  │  Gemini · Sarvam TTS  │   │
│  │      Sarvam STT       │   │
│  └───────────────────────┘   │
│       │                      │
│  ┌────▼────┐                 │
│  │ SQLite  │                 │
│  └─────────┘                 │
└──────────────────────────────┘
```

**Backend** — Python / FastAPI with async SQLite for session state and conversation logging.  
**Frontend** — React 18 with Chakra UI for the interface, WebSocket for real-time voice communication.  
**AI** — Google Gemini (via OpenRouter) for generating tutor dialogue; Sarvam AI for Indian English/Hindi text-to-speech and speech-to-text.

## Features

- **Voice-first learning** — the tutor speaks and the learner responds via microphone; full transcript displayed alongside audio
- **Structured curriculum** — lessons are broken into sections and steps with types like `teach`, `teach_and_ask`, `reflect`, `scenario`, and `summarize`
- **Bilingual support** — English and Hindi, with language-specific prompts and voice synthesis
- **Session persistence** — pause and resume lessons; progress tracked per-section in SQLite
- **Adjustable speech speed** — control TTS playback pace (0.5× to 2×)
- **Section sidebar** — visual progress indicator showing completed, in-progress, and upcoming sections
- **Conversation logging** — every tutor and learner turn is stored for review

## Project Structure

```
ai-leadership-tutor/
├── backend/
│   ├── main.py                 # FastAPI app, CORS, lifespan
│   ├── config.py               # Pydantic settings (env vars)
│   ├── models.py               # Request/response schemas, WS message types
│   ├── database.py             # Async SQLite helpers (sessions, progress, logs)
│   ├── db/
│   │   └── schema.sql          # Table definitions
│   ├── curriculum/
│   │   └── foundations-of-leadership.json  # Lesson content
│   ├── routers/
│   │   ├── modules.py          # GET /api/modules
│   │   ├── sessions.py         # CRUD /api/sessions
│   │   └── conversation.py     # WebSocket /ws/conversation/:id
│   └── services/
│       ├── gemini.py           # OpenRouter / Gemini chat completions
│       ├── sarvam_tts.py       # Sarvam AI text-to-speech
│       ├── sarvam_stt.py       # Sarvam AI speech-to-text
│       └── tutor_engine.py     # Curriculum state machine + prompt builder
├── frontend/
│   ├── package.json            # React, Chakra UI, Framer Motion
│   ├── vite.config.js          # Dev proxy to backend
│   └── src/
│       ├── main.jsx            # App entry, routing
│       ├── theme.js            # Chakra UI theme (Outfit font, brand colors)
│       ├── lib/api.js          # REST API client
│       ├── hooks/
│       │   ├── useWebSocket.js # WebSocket connection + message handling
│       │   └── useVoice.js     # MediaRecorder wrapper for mic input
│       ├── pages/
│       │   ├── Home.jsx        # Module listing, language picker, session resume
│       │   ├── Lesson.jsx      # Voice conversation interface
│       │   └── Progress.jsx    # Section-by-section completion view
│       └── components/
│           ├── MicButton.jsx   # Record button
│           ├── SectionSidebar.jsx  # Lesson outline drawer
│           ├── SpeedControl.jsx    # TTS pace slider
│           ├── StatusBar.jsx       # Thinking/listening/transcribing indicator
│           ├── Transcript.jsx      # Chat-style message log
│           └── TutorAvatar.jsx     # Animated tutor avatar
├── scripts/
│   └── init_db.py              # Standalone DB initialization
├── docs/plans/                 # Design and implementation notes
├── requirements.txt            # Python dependencies
└── .env.example                # Required environment variables
```

## Prerequisites

- **Python 3.11+**
- **Node.js 18+** and npm
- An **OpenRouter** API key (for Gemini model access)
- A **Sarvam AI** API key (for Indian-language TTS and STT)

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/kvsdileep/ai-leadership-tutor.git
cd ai-leadership-tutor
```

### 2. Set up environment variables

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```
OPENROUTER_API_KEY=your-openrouter-key-here
SARVAM_API_KEY=your-sarvam-key-here
DATABASE_URL=sqlite:///./tutor.db
```

### 3. Install and run the backend

```bash
pip install -r requirements.txt
python scripts/init_db.py
uvicorn backend.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`. You can verify with `GET /api/health`.

### 4. Install and run the frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend dev server starts at `http://localhost:5173` and proxies API/WebSocket requests to the backend.

### 5. Open in browser

Navigate to `http://localhost:5173`, pick a language, and start a lesson. Make sure your microphone is accessible.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/modules` | List available curriculum modules |
| `GET` | `/api/modules/:id` | Get module details |
| `POST` | `/api/sessions` | Create a new learning session |
| `GET` | `/api/sessions` | List active/paused sessions |
| `GET` | `/api/sessions/:id` | Get session details |
| `GET` | `/api/sessions/:id/progress` | Get section-by-section progress |
| `WS` | `/ws/conversation/:id` | Real-time voice conversation |

### WebSocket Message Types

**Client → Server:** `start`, `audio` (binary), `skip`, `set_pace`, `pause`  
**Server → Client:** `tutor_text`, `tutor_audio`, `learner_text`, `status`, `progress`, `curriculum_info`, `section_complete`, `module_complete`, `error`

## Curriculum

Lessons are defined as JSON files in `backend/curriculum/`. The included module — **Foundations of Leadership** — contains 5 sections across 16 steps covering topics like leadership styles, self-awareness, giving feedback, and personal commitment.

Each step has a `type` that controls the conversation flow:

| Step Type | Behavior |
|-----------|----------|
| `teach` | Tutor speaks, then auto-advances |
| `teach_and_ask` | Tutor speaks, waits for learner response |
| `reflect` | Tutor prompts self-reflection, waits for response |
| `scenario` | Tutor presents a scenario, waits for learner's approach |
| `summarize` | Tutor wraps up the section, auto-advances |

## Tech Stack

**Backend:** FastAPI, aiosqlite, httpx, Pydantic, uvicorn, websockets  
**Frontend:** React 18, Chakra UI v2, Framer Motion, React Router v7, Vite  
**AI Services:** Google Gemini 3 Flash (via OpenRouter), Sarvam AI Bulbul v2 (TTS), Sarvam AI Saarika v2.5 (STT)

## License

No license specified.

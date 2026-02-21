# UX Fixes Design — AI Leadership Tutor

**Date:** 2026-02-21
**Status:** Approved

## Problems

1. Tutor responses are too verbose — feels like a lecture, not a conversation
2. No way to pause/resume — user loses progress if they leave
3. No sense of progress — feels like a free-flowing conversation, not a structured module
4. Voice is too slow — no way to control playback speed

## Fix 1: Crisper Responses (1-2 sentences max)

### Changes
- **System prompt:** Change "2-4 sentences" to "1-2 sentences. Never more than 2. This is spoken aloud — be direct."
- **max_tokens:** Reduce from 500 to 150 (hard cap)
- **Curriculum prompt_guidance:** Trim all "2-3 sentences" / "3-4 sentences" guidance to "1-2 sentences max"

### Files
- `backend/services/tutor_engine.py` — system prompt
- `backend/services/gemini.py` — default max_tokens
- `backend/curriculum/foundations-of-leadership.json` — prompt_guidance strings

## Fix 2: Pause & Resume from Exact Step

### Changes
- **WebSocket:** Handle `pause` message type — save position, set status to `paused`, close cleanly
- **Home page:** Show existing active/paused sessions with "Continue" button
- **Resume flow:** When WS connects to an existing session, read saved position and start from that step
- **Backend models:** Add `pause` to WSMessageType

### Files
- `backend/routers/conversation.py` — handle pause message, resume from saved position
- `backend/models.py` — add pause message type
- `frontend/src/pages/Home.jsx` — show existing sessions, continue button
- `frontend/src/pages/Lesson.jsx` — add Pause button
- `frontend/src/hooks/useWebSocket.js` — send pause message
- `frontend/src/lib/api.js` — fetch existing sessions (new endpoint or reuse)
- `backend/routers/sessions.py` — add endpoint to list active/paused sessions

## Fix 3: Sidebar with Section List

### Changes
- **Sidebar component:** Collapsible panel showing all sections with status icons
  - Completed: checkmark icon, green
  - Active: pulsing dot, coral
  - Upcoming: gray circle
  - Active section expanded to show individual steps
- **Mobile:** Drawer that slides from left, triggered by hamburger button
- **Desktop:** Fixed sidebar on left side
- **Data:** Uses existing `progress` WS messages + curriculum section/step data

### Files
- `frontend/src/components/SectionSidebar.jsx` — new component
- `frontend/src/pages/Lesson.jsx` — integrate sidebar layout
- `frontend/src/hooks/useWebSocket.js` — expose curriculum metadata (section titles, step counts)
- `backend/routers/conversation.py` — send full section list with titles on connect

## Fix 4: Voice Speed Slider

### Changes
- **Backend TTS:** Accept `pace` parameter, pass to Sarvam API
- **WebSocket:** Accept `set_pace` message from client, store in session state
- **Frontend:** Segmented speed control: 0.75x | 1x | 1.25x | 1.5x
  - Default: 1.25x (user finds 1.0 slow)
  - Stored in localStorage for persistence
  - Displayed in bottom control bar
- Speed change applies to next tutor message

### Files
- `backend/services/sarvam_tts.py` — add `pace` parameter
- `backend/routers/conversation.py` — track pace per session, handle `set_pace` message
- `backend/models.py` — add `set_pace` message type
- `frontend/src/components/SpeedControl.jsx` — new component
- `frontend/src/pages/Lesson.jsx` — integrate speed control
- `frontend/src/hooks/useWebSocket.js` — send set_pace message

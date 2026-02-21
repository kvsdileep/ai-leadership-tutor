# UX Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix 4 UX issues: verbose responses, no pause/resume, unclear progress, slow voice speed.

**Architecture:** All fixes are additive — no major refactors. Backend changes: system prompt + max_tokens tuning, new WS message types (pause, set_pace), new REST endpoint (list sessions). Frontend changes: new SectionSidebar and SpeedControl components, Pause button, Continue card on Home.

**Tech Stack:** FastAPI, Sarvam AI (pace param), React, Chakra UI

---

### Task 1: Crisper Responses — System Prompt + max_tokens

**Files:**
- Modify: `backend/services/tutor_engine.py:66-77`
- Modify: `backend/services/gemini.py:5`

**Step 1: Update system prompt in tutor_engine.py**

In `build_system_prompt()`, replace the current guidelines with tighter ones:

```python
def build_system_prompt(curriculum: dict, language: str) -> str:
    lang_name = "Hindi" if language == "hi" else "English"
    return f"""You are a warm, direct leadership tutor in a voice conversation.

Rules:
- Speak in {lang_name}. Maximum 1-2 sentences per turn. Never more than 2.
- This is spoken aloud — be crisp, not wordy.
- No bullet points, lists, or markdown. No filler praise like "Great question!"
- Be specific when affirming. Be genuinely curious when asking.
- Module: {curriculum['title']}"""
```

**Step 2: Lower default max_tokens in gemini.py**

Change line 5 from `max_tokens: int = 500` to `max_tokens: int = 150`.

**Step 3: Trim curriculum prompt_guidance**

In `backend/curriculum/foundations-of-leadership.json`, find all instances of "2-3 sentences", "3-4 sentences", "2-4 sentences" in `prompt_guidance` and `feedback_guidance` fields and replace with "1-2 sentences max". Remove any "Keep it to X sentences" — the system prompt already enforces this.

**Step 4: Test**

Run: `source venv/bin/activate && python -m uvicorn backend.main:app --port 8000 &`
Then: `curl -s http://localhost:8000/api/test/gemini`
Verify response is short (1-2 sentences).

**Step 5: Commit**

```bash
git add backend/services/tutor_engine.py backend/services/gemini.py backend/curriculum/foundations-of-leadership.json
git commit -m "fix: make tutor responses crisper (1-2 sentences, 150 token cap)"
```

---

### Task 2: Voice Speed Control — Backend (Sarvam pace param)

**Files:**
- Modify: `backend/services/sarvam_tts.py:11`
- Modify: `backend/models.py:60-74`

**Step 1: Add pace parameter to TTS function**

Update `text_to_speech` signature and body in `sarvam_tts.py`:

```python
async def text_to_speech(text: str, language: str = "en", pace: float = 1.25) -> str:
    """Convert text to speech using Sarvam AI. Returns base64 encoded audio."""
    config = LANGUAGE_CONFIG.get(language, LANGUAGE_CONFIG["en"])

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{settings.sarvam_base_url}/text-to-speech",
            headers={
                "api-subscription-key": settings.sarvam_api_key,
                "Content-Type": "application/json",
            },
            json={
                "text": text,
                "target_language_code": config["language_code"],
                "model": "bulbul:v2",
                "speaker": "anushka",
                "pace": pace,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["audios"][0]
```

**Step 2: Add WS message types in models.py**

Add to `WSMessageType` enum:

```python
    # Client -> Server
    audio = "audio"
    skip = "skip"
    start = "start"
    pause = "pause"             # Pause the lesson
    set_pace = "set_pace"       # Set voice speed
```

**Step 3: Commit**

```bash
git add backend/services/sarvam_tts.py backend/models.py
git commit -m "feat: add pace parameter to TTS and new WS message types"
```

---

### Task 3: Voice Speed Control — Frontend SpeedControl Component

**Files:**
- Create: `frontend/src/components/SpeedControl.jsx`

**Step 1: Create SpeedControl component**

```jsx
import { HStack, Button } from '@chakra-ui/react'

const SPEEDS = [0.75, 1, 1.25, 1.5]

export default function SpeedControl({ value, onChange }) {
  return (
    <HStack spacing={1}>
      {SPEEDS.map(speed => (
        <Button
          key={speed}
          size="xs"
          variant={value === speed ? 'solid' : 'ghost'}
          bg={value === speed ? 'brand.sage' : 'transparent'}
          fontWeight={value === speed ? 600 : 400}
          fontSize="xs"
          borderRadius="full"
          px={2}
          minW="auto"
          onClick={() => onChange(speed)}
        >
          {speed}x
        </Button>
      ))}
    </HStack>
  )
}
```

**Step 2: Commit**

```bash
git add frontend/src/components/SpeedControl.jsx
git commit -m "feat: add SpeedControl component"
```

---

### Task 4: Voice Speed — Wire Through WebSocket + Conversation Handler

**Files:**
- Modify: `frontend/src/hooks/useWebSocket.js`
- Modify: `frontend/src/pages/Lesson.jsx`
- Modify: `backend/routers/conversation.py:26-36,110,150`

**Step 1: Add sendPace to useWebSocket.js**

Add after `sendSkip`:

```javascript
const sendPace = useCallback((pace) => {
  const ws = wsRef.current
  if (!ws || ws.readyState !== WebSocket.OPEN) return
  ws.send(JSON.stringify({ type: 'set_pace', data: { pace } }))
}, [])
```

Return `sendPace` from the hook.

**Step 2: Add pace state and SpeedControl to Lesson.jsx**

Add state: `const [pace, setPace] = useState(() => parseFloat(localStorage.getItem('tutor_pace') || '1.25'))`

Add handler:
```javascript
const handlePaceChange = useCallback((newPace) => {
  setPace(newPace)
  localStorage.setItem('tutor_pace', String(newPace))
  sendPace(newPace)
}, [sendPace])
```

Add `<SpeedControl value={pace} onChange={handlePaceChange} />` in the bottom controls bar.

Send initial pace on connect: in `useWebSocket.js` `ws.onopen`, after sending start, also send `{ type: 'set_pace', data: { pace: initialPace } }`. Pass `initialPace` to `connect()`.

**Step 3: Handle set_pace and pass pace to TTS in conversation.py**

Add a `session_pace` variable initialized to `1.25` in the WS handler.

In the main loop, add handler:
```python
elif msg_type == "set_pace":
    pace_val = msg.get("data", {}).get("pace", 1.25)
    session_pace = max(0.5, min(2.0, float(pace_val)))
```

Update `send_tutor_message` to accept and pass `pace`:
```python
async def send_tutor_message(ws, text, language, pace=1.25):
    await send_json(ws, "tutor_text", {"text": text})
    await send_json(ws, "status", {"state": "synthesizing"})
    try:
        audio_b64 = await text_to_speech(text, language, pace=pace)
        await send_json(ws, "tutor_audio", {"audio": audio_b64})
    except Exception as e:
        logger.error(f"TTS error: {e}")
        await send_json(ws, "error", {"message": "Audio synthesis failed."})
```

Pass `session_pace` to all `send_tutor_message` calls.

**Step 4: Commit**

```bash
git add frontend/src/hooks/useWebSocket.js frontend/src/pages/Lesson.jsx backend/routers/conversation.py
git commit -m "feat: wire voice speed control end-to-end"
```

---

### Task 5: Pause & Resume — Backend

**Files:**
- Modify: `backend/routers/conversation.py` (main loop)
- Modify: `backend/routers/sessions.py`
- Modify: `frontend/src/lib/api.js`

**Step 1: Handle pause message in conversation.py**

In the main `while True` loop, add:
```python
elif msg_type == "pause":
    await update_session_status(db, session_id, "paused")
    await send_json(ws, "status", {"state": "paused"})
    await ws.close()
    break
```

**Step 2: Add list-sessions endpoint in sessions.py**

```python
@router.get("", response_model=list[SessionResponse])
async def list_sessions(status: str | None = None):
    db = await get_db()
    try:
        if status:
            cursor = await db.execute(
                "SELECT * FROM sessions WHERE status = ? ORDER BY updated_at DESC", (status,)
            )
        else:
            cursor = await db.execute(
                "SELECT * FROM sessions WHERE status IN ('active', 'paused') ORDER BY updated_at DESC"
            )
        rows = await cursor.fetchall()
    finally:
        await db.close()

    return [
        SessionResponse(
            id=r["id"], module_id=r["module_id"], language=Language(r["language"]),
            current_section=r["current_section"], current_step=r["current_step"],
            status=SessionStatus(r["status"]),
        ) for r in rows
    ]
```

**Step 3: Add fetchSessions to api.js**

```javascript
export async function fetchSessions() {
  const res = await fetch(`${API_BASE}/sessions`)
  if (!res.ok) throw new Error('Failed to fetch sessions')
  return res.json()
}
```

**Step 4: Make WS resume from saved position**

The conversation handler already reads `section_idx` and `step_idx` from the session DB on connect (lines 54-55), so resume works automatically. When reconnecting to a paused session, update status back to active:

After line 66 in conversation.py, add:
```python
if session["status"] == "paused":
    await update_session_status(db, session_id, "active")
```

**Step 5: Commit**

```bash
git add backend/routers/conversation.py backend/routers/sessions.py frontend/src/lib/api.js
git commit -m "feat: add pause/resume and list-sessions endpoint"
```

---

### Task 6: Pause & Resume — Frontend

**Files:**
- Modify: `frontend/src/hooks/useWebSocket.js`
- Modify: `frontend/src/pages/Lesson.jsx`
- Modify: `frontend/src/pages/Home.jsx`

**Step 1: Add sendPause to useWebSocket.js**

```javascript
const sendPause = useCallback(() => {
  const ws = wsRef.current
  if (!ws || ws.readyState !== WebSocket.OPEN) return
  ws.send(JSON.stringify({ type: 'pause' }))
}, [])
```

Return `sendPause` from the hook.

**Step 2: Add Pause button to Lesson.jsx**

Replace the "Back" button with a "Pause & Exit" button that calls `sendPause()` then navigates to `/`:

```jsx
<Button size="sm" variant="ghost" onClick={() => { sendPause(); navigate('/') }}>
  ⏸ Pause
</Button>
```

**Step 3: Show existing sessions on Home.jsx**

Add state: `const [sessions, setSessions] = useState([])`

Fetch on mount: `fetchSessions().then(setSessions)`

Render a "Continue" card above the module cards for each active/paused session:

```jsx
{sessions.map(s => (
  <Card key={s.id} w="100%" borderRadius="2rem" bg="brand.lavender">
    <CardBody p={6}>
      <HStack justify="space-between">
        <VStack align="start" spacing={0}>
          <Text fontWeight={600} fontSize="sm">Continue your session</Text>
          <Text fontSize="xs" color="brand.muted">
            Section {s.current_section + 1} · {s.status}
          </Text>
        </VStack>
        <Button size="sm" variant="primary" onClick={() => navigate(`/lesson/${s.id}`)}>
          Resume
        </Button>
      </HStack>
    </CardBody>
  </Card>
))}
```

**Step 4: Commit**

```bash
git add frontend/src/hooks/useWebSocket.js frontend/src/pages/Lesson.jsx frontend/src/pages/Home.jsx
git commit -m "feat: pause/resume UI with continue card on Home"
```

---

### Task 7: Section Sidebar — Send Curriculum Metadata via WS

**Files:**
- Modify: `backend/routers/conversation.py:68-75`

**Step 1: Send full section list on connect**

After line 75 in conversation.py (after the initial progress message), add a `curriculum_info` message:

```python
# Send curriculum structure for sidebar
sections_info = []
for i, sec in enumerate(curriculum["sections"]):
    sections_info.append({
        "index": i,
        "title": sec["title"],
        "title_hi": sec.get("title_hi", sec["title"]),
        "step_count": len(sec["steps"]),
    })
await send_json(ws, "curriculum_info", {"sections": sections_info})
```

**Step 2: Handle curriculum_info in useWebSocket.js**

Add state: `const [curriculumInfo, setCurriculumInfo] = useState(null)`

Add case in switch:
```javascript
case 'curriculum_info':
  setCurriculumInfo(data)
  break
```

Return `curriculumInfo` from the hook.

**Step 3: Commit**

```bash
git add backend/routers/conversation.py frontend/src/hooks/useWebSocket.js
git commit -m "feat: send curriculum structure via WS for sidebar"
```

---

### Task 8: Section Sidebar — Frontend Component

**Files:**
- Create: `frontend/src/components/SectionSidebar.jsx`

**Step 1: Create the sidebar component**

```jsx
import {
  Box, VStack, HStack, Text, Icon, Drawer, DrawerOverlay,
  DrawerContent, DrawerBody, DrawerCloseButton, useDisclosure,
  IconButton, Badge,
} from '@chakra-ui/react'
import { FaCheckCircle, FaCircle, FaDotCircle, FaBars } from 'react-icons/fa'

function SectionList({ sections, progress, sectionProgress }) {
  if (!sections) return null

  return (
    <VStack align="stretch" spacing={1} py={4} px={2}>
      <Text fontSize="xs" fontWeight={600} color="brand.muted" px={3} pb={2}>
        SECTIONS
      </Text>
      {sections.map((sec) => {
        const isActive = progress && progress.section_index === sec.index
        const isCompleted = sectionProgress?.[sec.index] === 'completed'
        const icon = isCompleted ? FaCheckCircle : isActive ? FaDotCircle : FaCircle
        const color = isCompleted ? 'green.400' : isActive ? '#FFB7B2' : 'gray.300'

        return (
          <Box key={sec.index}>
            <HStack px={3} py={2} borderRadius="lg" bg={isActive ? 'brand.sage' : 'transparent'} spacing={3}>
              <Icon as={icon} color={color} boxSize={3} flexShrink={0} />
              <Box flex={1}>
                <Text fontSize="sm" fontWeight={isActive ? 600 : 400} noOfLines={1}>
                  {sec.title}
                </Text>
                {isActive && progress && (
                  <Text fontSize="xs" color="brand.muted">
                    Step {progress.step_index + 1} of {sec.step_count}
                  </Text>
                )}
              </Box>
            </HStack>
          </Box>
        )
      })}
    </VStack>
  )
}

export default function SectionSidebar({ sections, progress, sectionProgress }) {
  const { isOpen, onOpen, onClose } = useDisclosure()

  return (
    <>
      <IconButton
        icon={<FaBars />}
        aria-label="Show sections"
        size="sm"
        variant="ghost"
        onClick={onOpen}
      />
      <Drawer placement="left" onClose={onClose} isOpen={isOpen} size="xs">
        <DrawerOverlay />
        <DrawerContent bg="brand.bg">
          <DrawerCloseButton />
          <DrawerBody p={0}>
            <SectionList sections={sections} progress={progress} sectionProgress={sectionProgress} />
          </DrawerBody>
        </DrawerContent>
      </Drawer>
    </>
  )
}
```

**Step 2: Commit**

```bash
git add frontend/src/components/SectionSidebar.jsx
git commit -m "feat: add SectionSidebar component"
```

---

### Task 9: Section Sidebar — Integrate into Lesson Page

**Files:**
- Modify: `frontend/src/pages/Lesson.jsx`
- Modify: `frontend/src/hooks/useWebSocket.js`

**Step 1: Track section completion status in useWebSocket.js**

Add state: `const [sectionProgress, setSectionProgress] = useState({})`

In the `section_complete` case, update:
```javascript
case 'section_complete':
  setSectionComplete(data)
  setSectionProgress(prev => ({ ...prev, [data.section_index]: 'completed' }))
  setTimeout(() => setSectionComplete(null), 3000)
  break
```

In the `progress` case, mark current section as in_progress:
```javascript
case 'progress':
  setProgress(data)
  setSectionProgress(prev => {
    const next = { ...prev }
    if (!next[data.section_index] || next[data.section_index] !== 'completed') {
      next[data.section_index] = 'in_progress'
    }
    return next
  })
  break
```

Return `sectionProgress` and `curriculumInfo` from the hook.

**Step 2: Add SectionSidebar to Lesson.jsx top bar**

Import SectionSidebar. Replace the back button area:

```jsx
<HStack>
  <SectionSidebar
    sections={curriculumInfo?.sections}
    progress={progress}
    sectionProgress={sectionProgress}
  />
  <Button size="sm" variant="ghost" onClick={() => { sendPause(); navigate('/') }}>
    ⏸ Pause
  </Button>
</HStack>
```

**Step 3: Commit**

```bash
git add frontend/src/pages/Lesson.jsx frontend/src/hooks/useWebSocket.js
git commit -m "feat: integrate section sidebar into lesson page"
```

---

### Task 10: Final Verification

**Step 1: Start backend**

```bash
cd /Users/growthschool/Downloads/aigf_c5/ai-leadership-tutor
source venv/bin/activate
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

**Step 2: Start frontend**

```bash
cd /Users/growthschool/Downloads/aigf_c5/ai-leadership-tutor/frontend
npm run dev
```

**Step 3: Build check**

```bash
cd /Users/growthschool/Downloads/aigf_c5/ai-leadership-tutor/frontend
npx vite build
```

Expected: build succeeds with no errors.

**Step 4: API smoke tests**

```bash
curl -s http://localhost:8000/api/health
curl -s http://localhost:8000/api/modules
curl -s http://localhost:8000/api/sessions
curl -s http://localhost:8000/api/test/gemini
```

All should return 200.

**Step 5: Push to GitHub**

```bash
git push origin main
```

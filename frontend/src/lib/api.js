const API_BASE = '/api'

export async function fetchModules() {
  const res = await fetch(`${API_BASE}/modules`)
  if (!res.ok) throw new Error('Failed to fetch modules')
  return res.json()
}

export async function fetchModule(moduleId) {
  const res = await fetch(`${API_BASE}/modules/${moduleId}`)
  if (!res.ok) throw new Error('Failed to fetch module')
  return res.json()
}

export async function createSession(moduleId, language = 'en') {
  const res = await fetch(`${API_BASE}/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ module_id: moduleId, language }),
  })
  if (!res.ok) throw new Error('Failed to create session')
  return res.json()
}

export async function fetchSession(sessionId) {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}`)
  if (!res.ok) throw new Error('Failed to fetch session')
  return res.json()
}

export async function fetchProgress(sessionId) {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}/progress`)
  if (!res.ok) throw new Error('Failed to fetch progress')
  return res.json()
}

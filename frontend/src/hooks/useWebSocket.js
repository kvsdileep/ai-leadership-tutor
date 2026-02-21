import { useRef, useState, useCallback, useEffect } from 'react'

export default function useWebSocket(sessionId) {
  const wsRef = useRef(null)
  const [status, setStatus] = useState('connecting') // connecting, connected, listening, thinking, synthesizing, transcribing, disconnected
  const [messages, setMessages] = useState([]) // { role: 'tutor'|'learner', text }
  const [progress, setProgress] = useState(null)
  const [error, setError] = useState(null)
  const [moduleComplete, setModuleComplete] = useState(false)
  const [sectionComplete, setSectionComplete] = useState(null)
  const audioQueueRef = useRef([])
  const isPlayingRef = useRef(false)

  const playNextAudio = useCallback(() => {
    if (audioQueueRef.current.length === 0) {
      isPlayingRef.current = false
      return
    }
    isPlayingRef.current = true
    const audioB64 = audioQueueRef.current.shift()
    const audio = new Audio(`data:audio/wav;base64,${audioB64}`)
    audio.onended = () => playNextAudio()
    audio.onerror = () => playNextAudio()
    audio.play().catch(() => playNextAudio())
  }, [])

  const queueAudio = useCallback((audioB64) => {
    audioQueueRef.current.push(audioB64)
    if (!isPlayingRef.current) {
      playNextAudio()
    }
  }, [playNextAudio])

  const connect = useCallback(() => {
    if (!sessionId) return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws/conversation/${sessionId}`
    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      setStatus('connected')
      // Send start message
      ws.send(JSON.stringify({ type: 'start' }))
    }

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data)
      const { type, data } = msg

      switch (type) {
        case 'tutor_text':
          setMessages(prev => [...prev, { role: 'tutor', text: data.text }])
          break
        case 'tutor_audio':
          queueAudio(data.audio)
          break
        case 'learner_text':
          setMessages(prev => [...prev, { role: 'learner', text: data.text }])
          break
        case 'status':
          setStatus(data.state)
          break
        case 'progress':
          setProgress(data)
          break
        case 'section_complete':
          setSectionComplete(data)
          setTimeout(() => setSectionComplete(null), 3000)
          break
        case 'module_complete':
          setModuleComplete(true)
          break
        case 'error':
          setError(data.message)
          setTimeout(() => setError(null), 5000)
          break
      }
    }

    ws.onclose = () => {
      setStatus('disconnected')
    }

    ws.onerror = () => {
      setError('Connection error')
      setStatus('disconnected')
    }
  }, [sessionId, queueAudio])

  const sendAudio = useCallback((audioBlob) => {
    const ws = wsRef.current
    if (!ws || ws.readyState !== WebSocket.OPEN) return
    // Send raw binary audio
    audioBlob.arrayBuffer().then(buffer => {
      ws.send(buffer)
    })
  }, [])

  const sendSkip = useCallback(() => {
    const ws = wsRef.current
    if (!ws || ws.readyState !== WebSocket.OPEN) return
    ws.send(JSON.stringify({ type: 'skip' }))
  }, [])

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
  }, [])

  useEffect(() => {
    return () => disconnect()
  }, [disconnect])

  return {
    connect,
    disconnect,
    sendAudio,
    sendSkip,
    status,
    messages,
    progress,
    error,
    moduleComplete,
    sectionComplete,
  }
}

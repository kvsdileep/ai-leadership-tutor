import { useEffect, useCallback, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Box, VStack, HStack, Text, Button, Flex, useToast,
  Alert, AlertIcon, Progress,
} from '@chakra-ui/react'
import TutorAvatar from '../components/TutorAvatar'
import Transcript from '../components/Transcript'
import MicButton from '../components/MicButton'
import StatusBar from '../components/StatusBar'
import SpeedControl from '../components/SpeedControl'
import useWebSocket from '../hooks/useWebSocket'
import useVoice from '../hooks/useVoice'

export default function Lesson() {
  const { sessionId } = useParams()
  const navigate = useNavigate()
  const toast = useToast()

  const {
    connect, disconnect, sendAudio, sendSkip, sendPace,
    status, messages, progress, error, moduleComplete, sectionComplete,
  } = useWebSocket(sessionId)

  const { isRecording, startRecording, stopRecording } = useVoice()

  const [pace, setPace] = useState(() => parseFloat(localStorage.getItem('tutor_pace') || '1.25'))

  const handlePaceChange = useCallback((newPace) => {
    setPace(newPace)
    localStorage.setItem('tutor_pace', String(newPace))
    sendPace(newPace)
  }, [sendPace])

  useEffect(() => {
    connect(pace)
    return () => disconnect()
  }, [connect, disconnect])

  useEffect(() => {
    if (error) {
      toast({ title: error, status: 'warning', duration: 4000 })
    }
  }, [error, toast])

  useEffect(() => {
    if (sectionComplete) {
      toast({
        title: `Section complete: ${sectionComplete.section_title}`,
        status: 'success',
        duration: 3000,
      })
    }
  }, [sectionComplete, toast])

  const handleMicStart = useCallback(async () => {
    try {
      await startRecording()
    } catch {
      toast({ title: 'Microphone access denied', status: 'error' })
    }
  }, [startRecording, toast])

  const handleMicStop = useCallback(async () => {
    const blob = await stopRecording()
    if (blob && blob.size > 0) {
      sendAudio(blob)
    }
  }, [stopRecording, sendAudio])

  const isTutorBusy = ['thinking', 'synthesizing', 'transcribing'].includes(status)
  const canRecord = status === 'listening' && !isRecording

  const progressPercent = progress
    ? ((progress.section_index / progress.total_sections) * 100)
    : 0

  return (
    <Flex direction="column" h="100vh" bg="brand.bg">
      {/* Top bar */}
      <HStack px={4} py={3} borderBottom="1px solid" borderColor="gray.100" justify="space-between">
        <Button size="sm" variant="ghost" onClick={() => navigate('/')}>
          ← Back
        </Button>
        {progress && (
          <VStack spacing={0} align="end">
            <Text fontSize="xs" color="brand.muted">
              Section {progress.section_index + 1} of {progress.total_sections}
            </Text>
            <Text fontSize="xs" color="brand.muted" fontWeight={500}>
              {progress.section_title}
            </Text>
          </VStack>
        )}
      </HStack>

      {/* Progress bar */}
      <Progress
        value={progressPercent}
        size="xs"
        bg="brand.sage"
        sx={{ '& > div': { bg: 'brand.coral' } }}
      />

      {/* Module complete banner */}
      {moduleComplete && (
        <Alert status="success" variant="subtle" justifyContent="center">
          <AlertIcon />
          <Text fontWeight={500}>Module complete! Well done.</Text>
          <Button
            size="sm"
            ml={4}
            variant="primary"
            onClick={() => navigate(`/progress/${sessionId}`)}
          >
            View Progress
          </Button>
        </Alert>
      )}

      {/* Tutor avatar */}
      <VStack py={4} spacing={2}>
        <TutorAvatar isSpeaking={status === 'synthesizing' || isTutorBusy} />
        <StatusBar status={status} />
      </VStack>

      {/* Transcript */}
      <Transcript messages={messages} />

      {/* Bottom controls */}
      <HStack
        px={4}
        py={4}
        borderTop="1px solid"
        borderColor="gray.100"
        justify="center"
        spacing={4}
        bg="white"
      >
        <SpeedControl value={pace} onChange={handlePaceChange} />
        <Button
          size="sm"
          variant="ghost"
          onClick={sendSkip}
          isDisabled={isTutorBusy || isRecording}
        >
          Skip →
        </Button>
        <MicButton
          isRecording={isRecording}
          isDisabled={isTutorBusy && !isRecording}
          onStart={handleMicStart}
          onStop={handleMicStop}
        />
        {moduleComplete && (
          <Button
            size="sm"
            variant="primary"
            onClick={() => navigate(`/progress/${sessionId}`)}
          >
            Done
          </Button>
        )}
      </HStack>
    </Flex>
  )
}

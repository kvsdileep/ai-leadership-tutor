import { HStack, Text, Spinner } from '@chakra-ui/react'

const STATUS_LABELS = {
  connecting: 'Connecting...',
  connected: 'Connected',
  listening: 'Your turn — tap the mic to speak',
  thinking: 'Tutor is thinking...',
  synthesizing: 'Generating voice...',
  transcribing: 'Processing your speech...',
  disconnected: 'Disconnected',
}

const ACTIVE_STATES = ['thinking', 'synthesizing', 'transcribing', 'connecting']

export default function StatusBar({ status }) {
  const label = STATUS_LABELS[status] || status
  const isActive = ACTIVE_STATES.includes(status)

  return (
    <HStack
      justify="center"
      py={2}
      px={4}
      bg="brand.sage"
      borderRadius="xl"
      spacing={2}
    >
      {isActive && <Spinner size="xs" color="brand.muted" />}
      <Text fontSize="sm" color="brand.muted" fontWeight={500}>
        {label}
      </Text>
    </HStack>
  )
}

import { IconButton } from '@chakra-ui/react'
import { keyframes } from '@emotion/react'
import { FaMicrophone, FaStop } from 'react-icons/fa'

const recording = keyframes`
  0%, 100% { box-shadow: 0 0 0 0 rgba(255,183,178,0.4); }
  50% { box-shadow: 0 0 0 12px rgba(255,183,178,0); }
`

export default function MicButton({ isRecording, isDisabled, onStart, onStop }) {
  return (
    <IconButton
      icon={isRecording ? <FaStop /> : <FaMicrophone />}
      aria-label={isRecording ? 'Stop recording' : 'Start recording'}
      onClick={isRecording ? onStop : onStart}
      isDisabled={isDisabled}
      size="lg"
      w="64px"
      h="64px"
      borderRadius="full"
      bg={isRecording ? 'red.400' : 'brand.coral'}
      color="white"
      fontSize="xl"
      _hover={{
        bg: isRecording ? 'red.500' : '#ffa49e',
        transform: 'scale(1.05)',
      }}
      _active={{ transform: 'scale(0.95)' }}
      animation={isRecording ? `${recording} 1.5s ease-in-out infinite` : 'none'}
      transition="all 0.2s"
    />
  )
}

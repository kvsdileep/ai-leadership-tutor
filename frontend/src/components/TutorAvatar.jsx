import { Box } from '@chakra-ui/react'
import { keyframes } from '@emotion/react'

const pulse = keyframes`
  0%, 100% { transform: scale(1); opacity: 0.7; }
  50% { transform: scale(1.15); opacity: 0.4; }
`

const glow = keyframes`
  0%, 100% { box-shadow: 0 0 20px rgba(255,183,178,0.3); }
  50% { box-shadow: 0 0 40px rgba(255,183,178,0.6); }
`

export default function TutorAvatar({ isSpeaking = false }) {
  return (
    <Box position="relative" display="inline-flex" alignItems="center" justifyContent="center">
      {/* Outer pulse ring */}
      {isSpeaking && (
        <Box
          position="absolute"
          w="120px"
          h="120px"
          borderRadius="full"
          bg="brand.coral"
          animation={`${pulse} 1.5s ease-in-out infinite`}
        />
      )}
      {/* Main avatar circle */}
      <Box
        w="100px"
        h="100px"
        borderRadius="full"
        bg="linear-gradient(135deg, #FFB7B2, #EFEDF4)"
        display="flex"
        alignItems="center"
        justifyContent="center"
        fontSize="2.5rem"
        position="relative"
        zIndex={1}
        animation={isSpeaking ? `${glow} 1.5s ease-in-out infinite` : 'none'}
        transition="box-shadow 0.3s"
      >
        🎓
      </Box>
    </Box>
  )
}

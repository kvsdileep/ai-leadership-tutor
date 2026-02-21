import { useRef, useEffect } from 'react'
import { VStack, Box, Text } from '@chakra-ui/react'

export default function Transcript({ messages }) {
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <VStack
      flex={1}
      w="100%"
      overflowY="auto"
      spacing={3}
      px={4}
      py={4}
      align="stretch"
      css={{
        '&::-webkit-scrollbar': { width: '4px' },
        '&::-webkit-scrollbar-thumb': { bg: '#E8EFE8', borderRadius: '2px' },
      }}
    >
      {messages.map((msg, i) => (
        <Box
          key={i}
          alignSelf={msg.role === 'tutor' ? 'flex-start' : 'flex-end'}
          maxW="85%"
        >
          <Box
            bg={msg.role === 'tutor' ? 'brand.sage' : 'brand.lavender'}
            px={5}
            py={3}
            borderRadius={msg.role === 'tutor' ? '1.5rem 1.5rem 1.5rem 0.25rem' : '1.5rem 1.5rem 0.25rem 1.5rem'}
          >
            <Text fontSize="sm" color="brand.muted" fontWeight={500} mb={1}>
              {msg.role === 'tutor' ? 'Tutor' : 'You'}
            </Text>
            <Text fontSize="md" lineHeight="tall">{msg.text}</Text>
          </Box>
        </Box>
      ))}
      <div ref={bottomRef} />
    </VStack>
  )
}

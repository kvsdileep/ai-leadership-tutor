import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box, VStack, Heading, Text, Button, Card, CardBody,
  HStack, Badge, Flex, ButtonGroup, useToast,
} from '@chakra-ui/react'
import { fetchModules, createSession, fetchSessions } from '../lib/api'

export default function Home() {
  const [modules, setModules] = useState([])
  const [sessions, setSessions] = useState([])
  const [language, setLanguage] = useState('en')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const toast = useToast()

  useEffect(() => {
    fetchModules().then(setModules).catch(() =>
      toast({ title: 'Failed to load modules', status: 'error' })
    )
    fetchSessions().then(setSessions).catch(() => {})
  }, [toast])

  const handleStart = async (moduleId) => {
    setLoading(true)
    try {
      const session = await createSession(moduleId, language)
      navigate(`/lesson/${session.id}`)
    } catch {
      toast({ title: 'Failed to start session', status: 'error' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <Box minH="100vh" bg="brand.bg" py={12} px={4}>
      <VStack maxW="600px" mx="auto" spacing={8}>
        {/* Header */}
        <VStack spacing={3} textAlign="center">
          <Text fontSize="4xl">🎓</Text>
          <Heading size="xl" fontWeight={700} letterSpacing="tight">
            AI Leadership Tutor
          </Heading>
          <Text color="brand.muted" fontSize="lg" maxW="460px">
            Learn leadership through voice conversations with an AI coach.
            Practice real scenarios, get personalized feedback.
          </Text>
        </VStack>

        {/* Language toggle */}
        <Box>
          <Text fontSize="sm" color="brand.muted" mb={2} textAlign="center">
            Choose your language / भाषा चुनें
          </Text>
          <ButtonGroup isAttached variant="outline" size="md">
            <Button
              onClick={() => setLanguage('en')}
              bg={language === 'en' ? 'brand.sage' : 'transparent'}
              fontWeight={language === 'en' ? 600 : 400}
              borderColor="brand.sage"
            >
              🇬🇧 English
            </Button>
            <Button
              onClick={() => setLanguage('hi')}
              bg={language === 'hi' ? 'brand.sage' : 'transparent'}
              fontWeight={language === 'hi' ? 600 : 400}
              borderColor="brand.sage"
            >
              🇮🇳 हिन्दी
            </Button>
          </ButtonGroup>
        </Box>

        {/* Existing sessions */}
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

        {/* Module cards */}
        {modules.map((mod) => (
          <Card key={mod.id} w="100%" borderRadius="2rem" overflow="hidden">
            <CardBody p={8}>
              <VStack align="start" spacing={4}>
                <VStack align="start" spacing={1}>
                  <Heading size="md" fontWeight={600}>
                    {language === 'hi' ? mod.title_hi : mod.title}
                  </Heading>
                  <Text color="brand.muted" fontSize="sm">
                    {mod.description}
                  </Text>
                </VStack>

                <Flex gap={2} wrap="wrap">
                  <Badge bg="brand.lavender" color="brand.dark" borderRadius="full" px={3} py={1}>
                    {mod.section_count} sections
                  </Badge>
                  <Badge bg="brand.sage" color="brand.dark" borderRadius="full" px={3} py={1}>
                    ~{mod.estimated_minutes} min
                  </Badge>
                  <Badge bg="brand.coral" color="brand.dark" borderRadius="full" px={3} py={1} opacity={0.9}>
                    Voice conversation
                  </Badge>
                </Flex>

                <Button
                  variant="primary"
                  w="100%"
                  onClick={() => handleStart(mod.id)}
                  isLoading={loading}
                  loadingText="Starting..."
                  size="lg"
                >
                  {language === 'hi' ? 'सीखना शुरू करें' : 'Start Learning'}
                </Button>
              </VStack>
            </CardBody>
          </Card>
        ))}

        <Text fontSize="xs" color="brand.muted" textAlign="center">
          Uses your microphone for voice conversations. Works best in a quiet environment.
        </Text>
      </VStack>
    </Box>
  )
}

import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Box, VStack, Heading, Text, Button, Card, CardBody,
  HStack, Badge, List, ListItem, ListIcon, useToast,
} from '@chakra-ui/react'
import { FaCheckCircle, FaCircle, FaPlayCircle } from 'react-icons/fa'
import { fetchProgress } from '../lib/api'

const STATUS_ICON = {
  completed: FaCheckCircle,
  in_progress: FaPlayCircle,
  not_started: FaCircle,
}

const STATUS_COLOR = {
  completed: 'green.400',
  in_progress: 'brand.coral',
  not_started: 'gray.300',
}

export default function Progress() {
  const { sessionId } = useParams()
  const navigate = useNavigate()
  const toast = useToast()
  const [data, setData] = useState(null)

  useEffect(() => {
    fetchProgress(sessionId).then(setData).catch(() =>
      toast({ title: 'Failed to load progress', status: 'error' })
    )
  }, [sessionId, toast])

  if (!data) {
    return (
      <Box minH="100vh" bg="brand.bg" display="flex" alignItems="center" justifyContent="center">
        <Text color="brand.muted">Loading...</Text>
      </Box>
    )
  }

  const completedCount = data.sections.filter(s => s.status === 'completed').length

  return (
    <Box minH="100vh" bg="brand.bg" py={12} px={4}>
      <VStack maxW="500px" mx="auto" spacing={8}>
        <VStack spacing={2} textAlign="center">
          <Text fontSize="3xl">
            {data.overall_status === 'completed' ? '🎉' : '📊'}
          </Text>
          <Heading size="lg" fontWeight={700}>
            {data.overall_status === 'completed' ? 'Session Complete!' : 'Your Progress'}
          </Heading>
          <HStack>
            <Badge bg="brand.sage" borderRadius="full" px={3} py={1}>
              {completedCount} / {data.sections.length} sections
            </Badge>
          </HStack>
        </VStack>

        <Card w="100%" borderRadius="2rem">
          <CardBody p={6}>
            <List spacing={4}>
              {data.sections.map((section) => (
                <ListItem key={section.section_id} display="flex" alignItems="center">
                  <ListIcon
                    as={STATUS_ICON[section.status]}
                    color={STATUS_COLOR[section.status]}
                    fontSize="lg"
                  />
                  <Box>
                    <Text fontWeight={500}>{section.title}</Text>
                    <Text fontSize="xs" color="brand.muted" textTransform="capitalize">
                      {section.status.replace('_', ' ')}
                    </Text>
                  </Box>
                </ListItem>
              ))}
            </List>
          </CardBody>
        </Card>

        <VStack spacing={3} w="100%">
          {data.overall_status !== 'completed' && (
            <Button
              variant="primary"
              w="100%"
              onClick={() => navigate(`/lesson/${sessionId}`)}
            >
              Continue Learning
            </Button>
          )}
          <Button
            variant="ghost"
            w="100%"
            onClick={() => navigate('/')}
          >
            ← Back to Home
          </Button>
        </VStack>
      </VStack>
    </Box>
  )
}

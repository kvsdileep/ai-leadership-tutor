import {
  Box, VStack, HStack, Text, Icon, Drawer, DrawerOverlay,
  DrawerContent, DrawerBody, DrawerCloseButton, useDisclosure,
  IconButton,
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

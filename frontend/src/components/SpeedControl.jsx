import { HStack, Button } from '@chakra-ui/react'

const SPEEDS = [0.75, 1, 1.25, 1.5]

export default function SpeedControl({ value, onChange }) {
  return (
    <HStack spacing={1}>
      {SPEEDS.map(speed => (
        <Button
          key={speed}
          size="xs"
          variant={value === speed ? 'solid' : 'ghost'}
          bg={value === speed ? 'brand.sage' : 'transparent'}
          fontWeight={value === speed ? 600 : 400}
          fontSize="xs"
          borderRadius="full"
          px={2}
          minW="auto"
          onClick={() => onChange(speed)}
        >
          {speed}x
        </Button>
      ))}
    </HStack>
  )
}

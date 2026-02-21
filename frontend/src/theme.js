import { extendTheme } from '@chakra-ui/react'

const theme = extendTheme({
  fonts: {
    heading: `'Outfit', sans-serif`,
    body: `'Outfit', sans-serif`,
  },
  colors: {
    brand: {
      bg: '#FDFCF8',
      sage: '#E8EFE8',
      lavender: '#EFEDF4',
      coral: '#FFB7B2',
      dark: '#292524',
      muted: '#78716C',
      warmWhite: '#FFF9F5',
    },
  },
  styles: {
    global: {
      body: {
        bg: '#FDFCF8',
        color: '#292524',
      },
    },
  },
  components: {
    Button: {
      variants: {
        primary: {
          bg: '#FFB7B2',
          color: '#292524',
          fontWeight: 600,
          borderRadius: '2rem',
          px: 8,
          py: 6,
          _hover: { bg: '#ffa49e', transform: 'translateY(-1px)', boxShadow: 'md' },
          _active: { bg: '#ff9690', transform: 'translateY(0)' },
        },
        ghost: {
          color: '#78716C',
          _hover: { bg: '#E8EFE8' },
        },
      },
    },
    Card: {
      baseStyle: {
        container: {
          borderRadius: '2rem',
          boxShadow: '0 2px 16px rgba(0,0,0,0.04)',
          bg: 'white',
        },
      },
    },
  },
})

export default theme

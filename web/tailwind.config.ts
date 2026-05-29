import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        background: '#f6f7f9',
        foreground: '#1b1b1b',
        accent: '#d27684',
        'accent-hover': '#c4606e',
        muted: '#919191',
        border: '#e6e6e6',
        white: '#ffffff',
      },
      fontFamily: {
        serif: ['Source Serif Pro', 'Georgia', 'serif'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}

export default config

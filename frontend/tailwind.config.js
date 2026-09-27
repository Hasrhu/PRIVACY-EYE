/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        red:    { DEFAULT: '#dc2626', deep: '#991b1b', light: '#ef4444', glow: 'rgba(220,38,38,0.25)' },
        black:  { DEFAULT: '#0a0a0a', 2: '#111111', 3: '#1a1a1a', 4: '#222222' },
        muted:  { DEFAULT: '#6b7280', 2: '#9ca3af' },
      },
      fontFamily: {
        sans:    ['Inter', 'system-ui', 'sans-serif'],
        display: ['Bebas Neue', 'sans-serif'],
        mono:    ['JetBrains Mono', 'monospace'],
      },
      letterSpacing: { wide2: '0.08em', wide3: '0.12em', wide4: '0.15em' },
      animation: {
        'pulse-red': 'pulse-red 2s infinite',
        'scan':      'scan 2s linear infinite',
        'fade-up':   'fadeUp 0.6s ease forwards',
      },
    },
  },
  plugins: [],
}

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#fff7ed',
          100: '#ffedd5',
          200: '#fed7aa',
          300: '#fdba74',
          400: '#fb923c',
          500: '#f97316',
          600: '#ea580c',
          700: '#c2410c',
          800: '#9a3412',
          900: '#7c2d12',
        },
        app: {
          dark: '#1a1a1a',
          darker: '#0f0f0f',
          surface: '#242424',
          'surface-light': '#2a2a2a',
          border: '#333333',
          'border-light': '#404040',
          accent: '#ff6b35',
          'accent-hover': '#ff8555',
          text: '#ffffff',
          'text-secondary': '#b3b3b3',
          'text-tertiary': '#808080',
        },
      },
      fontFamily: {
        sans: ['-apple-system', 'BlinkMacSystemFont', 'SF Pro Display', 'SF Pro Text', 'Helvetica Neue', 'Arial', 'sans-serif'],
        display: ['-apple-system', 'BlinkMacSystemFont', 'SF Pro Display', 'Helvetica Neue', 'Arial', 'sans-serif'],
      },
      fontSize: {
        'large-title': ['34px', { lineHeight: '41px', fontWeight: '700' }],
        'title-1': ['28px', { lineHeight: '34px', fontWeight: '700' }],
        'title-2': ['22px', { lineHeight: '28px', fontWeight: '700' }],
        'title-3': ['20px', { lineHeight: '25px', fontWeight: '600' }],
        headline: ['17px', { lineHeight: '22px', fontWeight: '600' }],
        body: ['17px', { lineHeight: '22px', fontWeight: '400' }],
        callout: ['16px', { lineHeight: '21px', fontWeight: '400' }],
        subhead: ['15px', { lineHeight: '20px', fontWeight: '400' }],
        footnote: ['13px', { lineHeight: '18px', fontWeight: '400' }],
        caption: ['12px', { lineHeight: '16px', fontWeight: '400' }],
      },
    },
  },
  plugins: [],
}


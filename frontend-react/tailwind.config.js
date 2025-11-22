/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                void: '#0a0a0a',
                amber: '#ffb703',
                electric: '#219ebc',
                breach: '#d00000',
                glass: 'rgba(255, 255, 255, 0.1)',
                'glass-border': 'rgba(255, 255, 255, 0.2)',
            },
            fontFamily: {
                mono: ['Consolas', 'Monaco', 'monospace'],
                sans: ['Inter', 'sans-serif'],
            },
            animation: {
                'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                'glow': 'glow 2s ease-in-out infinite alternate',
            },
            keyframes: {
                glow: {
                    '0%': { boxShadow: '0 0 5px #219ebc' },
                    '100%': { boxShadow: '0 0 20px #219ebc, 0 0 10px #219ebc' },
                }
            }
        },
    },
    plugins: [],
}

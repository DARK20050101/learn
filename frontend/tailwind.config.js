/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#17231d',
        paper: '#f6f7f2',
        leaf: { 50: '#edf5ef', 100: '#d9eadf', 500: '#4f8062', 600: '#3d6b50', 700: '#315540' },
        coral: '#e47b62',
        sand: '#e8dfcf',
      },
      boxShadow: { soft: '0 12px 40px rgba(27, 47, 36, .08)' },
      fontFamily: { sans: ['Inter', 'PingFang SC', 'Microsoft YaHei', 'sans-serif'] },
    },
  },
  plugins: [],
}

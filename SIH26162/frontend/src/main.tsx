import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import 'leaflet/dist/leaflet.css'
import './index.css'
import App from './App'

// Initialize saved theme or default to dark
const savedTheme = localStorage.getItem('sih_theme')
if (savedTheme === 'light') {
  document.documentElement.classList.add('light')
  document.documentElement.classList.remove('dark')
  document.documentElement.setAttribute('data-theme', 'light')
} else {
  document.documentElement.classList.add('dark')
  document.documentElement.classList.remove('light')
  document.documentElement.setAttribute('data-theme', 'dark')
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)

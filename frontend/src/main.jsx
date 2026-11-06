import { StrictMode } from 'react'
import { MotionConfig } from 'motion/react'
import { createRoot } from 'react-dom/client'
import './index.css'
import { BrowserRouter } from 'react-router-dom'
import AppRoutes from './AppRoutes.jsx'

// Apply the saved presentation preference on every route, including a direct landing visit.
try {
  document.documentElement.dataset.theme = localStorage.getItem('omnikpi-theme') === 'dark' ? 'dark' : 'light'
} catch {
  document.documentElement.dataset.theme = 'light'
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <MotionConfig reducedMotion="user"><BrowserRouter><AppRoutes /></BrowserRouter></MotionConfig>
  </StrictMode>,
)

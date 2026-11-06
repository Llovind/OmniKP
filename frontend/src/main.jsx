import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Landing from './Landing.jsx'
import Evaluation from './Evaluation.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter><Routes><Route path="/" element={<Landing />} /><Route path="/app" element={<App />} /><Route path="/evaluation" element={<Evaluation />} /></Routes></BrowserRouter>
  </StrictMode>,
)

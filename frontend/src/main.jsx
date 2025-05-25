import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
// import './index.css'
// import App from './App.jsx'
// import ConnectionTest from './ConnectionTest'
import Speech from './Speech'
import FileUpload from './FileUpload'
import ConnectionTest from './Modified_FE'
import Location from './Location'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ConnectionTest />
  </StrictMode>,
)

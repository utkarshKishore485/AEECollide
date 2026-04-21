import { useState, useEffect } from 'react'
import Header from './components/Header'
import SiteSelectionTab from './components/SiteSelection/SiteSelectionTab'
import DispatchTab from './components/Dispatch/DispatchTab'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

function App() {
  const [activeTab, setActiveTab] = useState('sites')
  const [lastUpdated, setLastUpdated] = useState(new Date())

  useEffect(() => {
    const interval = setInterval(() => {
      setLastUpdated(new Date())
    }, 60000)
    return () => clearInterval(interval)
  }, [])

  const getTimeSinceUpdate = () => {
    const diff = Math.floor((new Date() - lastUpdated) / 60000)
    if (diff < 1) return 'Just now'
    return `${diff} min ago`
  }

  return (
    <div className="app-container">
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        lastUpdated={getTimeSinceUpdate()}
      />
      <div className="tab-content">
        {activeTab === 'sites' ? (
          <SiteSelectionTab apiBase={API_BASE} />
        ) : (
          <DispatchTab apiBase={API_BASE} />
        )}
      </div>
    </div>
  )
}

export default App

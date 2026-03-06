import { useState, useEffect } from 'react'
import { getUserProfile } from '../api/client'
import './Sidebar.css'

const QUICK_PROMPTS = [
  { label: '🧮 Calculate', text: 'What is 2024 * 7 + 365?' },
  { label: '🔍 Web Search', text: 'Search for the latest news in AI' },
  { label: '💼 Find Jobs', text: 'Find backend engineering jobs in Berlin' },
  { label: '🧠 About Me', text: 'What do you remember about me?' },
]

export default function Sidebar({ session, isOpen, onClose, onNewChat }) {
  const [profile, setProfile] = useState(null)

  useEffect(() => {
    if (isOpen && session) {
      getUserProfile(session)
        .then(setProfile)
        .catch(() => setProfile(null))
    }
  }, [isOpen, session])

  return (
    <>
      {/* Overlay */}
      {isOpen && <div className="sidebar-overlay" onClick={onClose} />}

      <aside className={`sidebar ${isOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <h2>AI Agent System</h2>
          <button className="icon-btn" onClick={onClose}>✕</button>
        </div>

        <nav className="sidebar-section">
          <h3>Actions</h3>
          <button className="sidebar-btn primary" onClick={onNewChat}>
            ＋ New Chat
          </button>
        </nav>

        <nav className="sidebar-section">
          <h3>Quick Prompts</h3>
          {QUICK_PROMPTS.map(qp => (
            <button
              key={qp.label}
              className="sidebar-btn"
              onClick={() => {
                // Copy to clipboard and close
                navigator.clipboard?.writeText(qp.text)
                onClose()
              }}
              title={qp.text}
            >
              {qp.label}
            </button>
          ))}
        </nav>

        {profile && (
          <div className="sidebar-section">
            <h3>Your Profile</h3>
            <div className="profile-card">
              {profile.name && <p><span>Name</span>{profile.name}</p>}
              {profile.location && <p><span>Location</span>{profile.location}</p>}
              {profile.skills?.length > 0 && (
                <p><span>Skills</span>{profile.skills.join(', ')}</p>
              )}
              {profile.facts?.length > 0 && (
                <div>
                  <span>Facts</span>
                  <ul>
                    {profile.facts.slice(-5).map((f, i) => <li key={i}>{f}</li>)}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}

        <div className="sidebar-footer">
          <p>Session: <code>{session?.slice(0, 8)}…</code></p>
          <p>Powered by Ollama + Qdrant</p>
        </div>
      </aside>
    </>
  )
}

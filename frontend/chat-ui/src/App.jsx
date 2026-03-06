import { useState, useEffect, useRef, useCallback } from 'react'
import { v4 as uuidv4 } from 'uuid'
import { sendMessage, clearHistory } from './api/client'
import MessageBubble from './components/MessageBubble'
import TypingIndicator from './components/TypingIndicator'
import Sidebar from './components/Sidebar'
import './App.css'

// Persist session ID across page reloads
function getSession() {
  let s = localStorage.getItem('agent_session')
  if (!s) { s = uuidv4(); localStorage.setItem('agent_session', s) }
  return s
}

export default function App() {
  const [session]           = useState(getSession)
  const [messages, setMsgs] = useState([
    { role: 'assistant', content: '👋 Hi! I\'m your AI Agent. I have memory, can search the web, do calculations, and find jobs. How can I help you today?' }
  ])
  const [input, setInput]   = useState('')
  const [loading, setLoad]  = useState(false)
  const [sidebarOpen, setSidebar] = useState(false)
  const bottomRef = useRef(null)
  const inputRef  = useRef(null)

  // Auto-scroll to latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const send = useCallback(async () => {
    const text = input.trim()
    if (!text || loading) return

    setMsgs(m => [...m, { role: 'user', content: text }])
    setInput('')
    setLoad(true)

    try {
      const reply = await sendMessage(session, text)
      setMsgs(m => [...m, { role: 'assistant', content: reply }])
    } catch (err) {
      const errMsg = err.response?.data?.detail || err.message || 'Unknown error'
      setMsgs(m => [...m, {
        role: 'assistant',
        content: `⚠️ Error: ${errMsg}`,
        error: true
      }])
    } finally {
      setLoad(false)
      inputRef.current?.focus()
    }
  }, [input, loading, session])

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() }
  }

  const handleNewChat = async () => {
    await clearHistory(session)
    setMsgs([{ role: 'assistant', content: '🔄 Chat cleared! Starting fresh. How can I help?' }])
  }

  return (
    <div className="app-layout">
      <Sidebar
        session={session}
        isOpen={sidebarOpen}
        onClose={() => setSidebar(false)}
        onNewChat={handleNewChat}
      />

      <div className="chat-container">
        {/* Header */}
        <header className="chat-header">
          <button className="icon-btn" onClick={() => setSidebar(o => !o)} title="Toggle sidebar">
            <span>☰</span>
          </button>
          <div className="header-title">
            <span className="agent-icon">🤖</span>
            <div>
              <h1>AI Agent</h1>
              <p className="subtitle">Memory · Tools · Planning · Reflection</p>
            </div>
          </div>
          <div className="status-dot" title="Connected" />
        </header>

        {/* Messages */}
        <main className="messages-area">
          {messages.map((msg, i) => (
            <MessageBubble key={i} role={msg.role} content={msg.content} error={msg.error} />
          ))}
          {loading && <TypingIndicator />}
          <div ref={bottomRef} />
        </main>

        {/* Input */}
        <footer className="input-area">
          <div className="input-box">
            <textarea
              ref={inputRef}
              className="chat-input"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKey}
              placeholder="Ask me anything… (Shift+Enter for new line)"
              rows={1}
              disabled={loading}
            />
            <button
              className={`send-btn ${loading ? 'sending' : ''}`}
              onClick={send}
              disabled={loading || !input.trim()}
              title="Send message"
            >
              {loading ? '⏳' : '➤'}
            </button>
          </div>
          <p className="input-hint">
            Try: "What is 144 * 8?" · "Search for Python news" · "Find backend jobs in Berlin"
          </p>
        </footer>
      </div>
    </div>
  )
}

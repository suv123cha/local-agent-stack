import './MessageBubble.css'

// Very simple markdown-like renderer (bold, code, line breaks)
function renderContent(text) {
  const parts = text.split(/(```[\s\S]*?```|`[^`]+`)/g)
  return parts.map((part, i) => {
    if (part.startsWith('```') && part.endsWith('```')) {
      const code = part.slice(3, -3).replace(/^\w+\n/, '')
      return <pre key={i} className="code-block"><code>{code}</code></pre>
    }
    if (part.startsWith('`') && part.endsWith('`')) {
      return <code key={i} className="inline-code">{part.slice(1, -1)}</code>
    }
    // Render newlines and basic bold
    return part.split('\n').map((line, j) => {
      const bold = line.replace(/\*\*(.+?)\*\*/g, (_, t) => `<b>${t}</b>`)
      return (
        <span key={`${i}-${j}`}>
          <span dangerouslySetInnerHTML={{ __html: bold }} />
          {j < part.split('\n').length - 1 && <br />}
        </span>
      )
    })
  })
}

export default function MessageBubble({ role, content, error }) {
  const isUser = role === 'user'
  return (
    <div className={`bubble-row ${isUser ? 'user' : 'assistant'}`}>
      <div className="avatar">
        {isUser ? '🧑' : '🤖'}
      </div>
      <div className={`bubble ${isUser ? 'user-bubble' : 'ai-bubble'} ${error ? 'error-bubble' : ''}`}>
        {renderContent(content)}
      </div>
    </div>
  )
}

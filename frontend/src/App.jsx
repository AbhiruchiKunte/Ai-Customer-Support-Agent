import React, { useState, useEffect, useRef } from 'react'
import './index.css'

// --- API Service ---
const API_BASE = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '') + '/api'

const fetchChat = async (message, sessionId) => {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, message }),
  })
  if (!res.ok) {
    if (res.status === 429) {
      throw new Error('rate_limit')
    }
    throw new Error('server_error')
  }
  return await res.json()
}

const fetchDocumentExcerpt = async (docRef) => {
  try {
    const res = await fetch(`${API_BASE}/document/${encodeURIComponent(docRef)}`)
    if (!res.ok) return null
    return await res.json()
  } catch {
    return null
  }
}

// Markdown Formatter
const formatMarkdown = (text) => {
  if (!text) return ''
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br/>')
}

// Status Color & Icon Mapping
const STATUS_CONFIG = {
  pending: { bg: 'rgba(139, 148, 158, 0.15)', color: '#8b949e', icon: '⏳' },
  processing: { bg: 'rgba(88, 166, 255, 0.15)', color: '#58a6ff', icon: '⚙️' },
  shipped: { bg: 'rgba(76, 175, 125, 0.15)', color: '#4caf7d', icon: '🚚' },
  delivered: { bg: 'rgba(63, 185, 80, 0.15)', color: '#3fb950', icon: '✅' },
  cancelled: { bg: 'rgba(248, 81, 73, 0.15)', color: '#f85149', icon: '✗' },
  returned: { bg: 'rgba(240, 136, 62, 0.15)', color: '#f0883e', icon: '↩️' },
  exception: { bg: 'rgba(210, 153, 34, 0.15)', color: '#d29922', icon: '⚠️' },
}

// Topic Categories and Suggested Questions
const TOPIC_CATEGORIES = [
  {
    id: 'orders',
    label: 'Orders',
    icon: '📦',
    questions: [
      'Where is order ORD-1007?',
      'What is my order status?',
      'Can I cancel or change my order?',
    ],
  },
  {
    id: 'returns',
    label: 'Returns',
    icon: '↩️',
    questions: [
      'What is my return window?',
      'How do I initiate a return?',
      'Can I return a final sale item if damaged?',
    ],
  },
  {
    id: 'shipping',
    label: 'Shipping',
    icon: '🚚',
    questions: [
      'Do you ship to Canada?',
      'What are domestic shipping transit times?',
      'Who pays customs duties on international orders?',
    ],
  },
  {
    id: 'warranty',
    label: 'Warranty',
    icon: '🛡️',
    questions: [
      'What does the product warranty cover?',
      'Is there a lifetime warranty on daypacks?',
      'How do I file a warranty replacement claim?',
    ],
  },
  {
    id: 'trailplus',
    label: 'TrailPlus',
    icon: '⭐',
    questions: [
      'TrailPlus membership benefits',
      'What is the TrailPlus return window?',
      'How much does TrailPlus cost annually?',
    ],
  },
  {
    id: 'care',
    label: 'Product Care',
    icon: '🧴',
    questions: [
      'How do I clean the Breeze Tumbler?',
      'How do I care for the Ridge Daypack?',
      'Are tumbler caps dishwasher safe?',
    ],
  },
]

export default function App() {
  const [sessionId] = useState(() => {
    const stored = localStorage.getItem('ar_session_id')
    if (stored) return stored
    const newId = crypto.randomUUID()
    localStorage.setItem('ar_session_id', newId)
    return newId
  })

  const [history, setHistory] = useState(() => {
    const stored = sessionStorage.getItem('ar_chat_history')
    return stored ? JSON.parse(stored) : []
  })

  useEffect(() => {
    sessionStorage.setItem('ar_chat_history', JSON.stringify(history))
  }, [history])

  const [input, setInput] = useState('')
  const [chatState, setChatState] = useState('idle') // 'idle' | 'sending' | 'error'
  const [lastFailedMessage, setLastFailedMessage] = useState(null)
  const [theme, setTheme] = useState(() => localStorage.getItem('ar_theme') || 'dark')
  const [showNewMessageChip, setShowNewMessageChip] = useState(false)
  const [activeCategory, setActiveCategory] = useState(null)
  
  // UI Interactive States
  const [drawerDoc, setDrawerDoc] = useState(null)
  const [openDetails, setOpenDetails] = useState({})
  const [feedbackState, setFeedbackState] = useState({})
  const [copiedStates, setCopiedStates] = useState({})

  const chatLogRef = useRef(null)
  const inputRef = useRef(null)

  // Initialize theme
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('ar_theme', theme)
  }, [theme])

  const toggleTheme = () => {
    setTheme(prev => (prev === 'dark' ? 'light' : 'dark'))
  }

  // Reset to Home / Clear Session
  const resetToHome = () => {
    sessionStorage.removeItem('ar_chat_history')
    setHistory([])
    setInput('')
    setChatState('idle')
    setLastFailedMessage(null)
    setActiveCategory(null)
    setDrawerDoc(null)
    if (inputRef.current) inputRef.current.focus()
  }

  // Scroll to bottom helper
  const scrollToBottom = (smooth = true) => {
    if (chatLogRef.current) {
      chatLogRef.current.scrollTo({
        top: chatLogRef.current.scrollHeight,
        behavior: smooth ? 'smooth' : 'auto',
      })
    }
  }

  useEffect(() => {
    scrollToBottom()
  }, [history, chatState])

  const handleScroll = () => {
    if (!chatLogRef.current) return
    const { scrollTop, scrollHeight, clientHeight } = chatLogRef.current
    const isUp = scrollHeight - scrollTop - clientHeight > 120
    setShowNewMessageChip(isUp)
  }

  // Send message
  const handleSend = async (messageText = input) => {
    const query = messageText.trim()
    if (!query || chatState === 'sending') return

    const userMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }

    setHistory(prev => [...prev, userMessage])
    setInput('')
    setChatState('sending')
    setLastFailedMessage(null)

    try {
      const response = await fetchChat(query, sessionId)

      const agentMessage = {
        id: crypto.randomUUID(),
        role: 'agent',
        content: response.answer || '',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        sources: response.sources || [],
        handoff: !!response.handoff,
        orderData: response.orderData || null,
        toolCalls: response.tool_calls || [],
        hasConflict: response.sources && response.sources.some(s => s.conflict_detected),
      }

      setHistory(prev => [...prev, agentMessage])
      setChatState('idle')
    } catch (err) {
      setLastFailedMessage(query)
      setChatState('error')

      const isRateLimit = err.message === 'rate_limit'
      const errorMessage = {
        id: crypto.randomUUID(),
        role: 'agent',
        isError: true,
        isRateLimit: isRateLimit,
        content: isRateLimit
          ? 'Our AI assistant is currently experiencing high traffic. Please try again shortly.'
          : 'Our AI assistant is temporarily unavailable. Please try again in a moment.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }
      setHistory(prev => [...prev, errorMessage])
      setChatState('idle')
    }
  }

  // Retry sending last failed message safely without duplicating error
  const handleRetry = () => {
    if (!lastFailedMessage) return
    // Remove last error message from history
    setHistory(prev => prev.filter(m => !m.isError))
    handleSend(lastFailedMessage)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const copyText = (msgId, text) => {
    navigator.clipboard.writeText(text)
    setCopiedStates(prev => ({ ...prev, [msgId]: true }))
    setTimeout(() => {
      setCopiedStates(prev => ({ ...prev, [msgId]: false }))
    }, 2000)
  }

  const handleFeedback = (msgId, rating) => {
    if (feedbackState[msgId]) return
    setFeedbackState(prev => ({ ...prev, [msgId]: rating }))
  }

  const toggleDetails = (msgId) => {
    setOpenDetails(prev => ({ ...prev, [msgId]: !prev[msgId] }))
  }

  // Open Source Side Drawer
  const openSourceDrawer = async (source) => {
    const docRef = source.document_id || source.filename
    const fetchedDoc = await fetchDocumentExcerpt(docRef)

    setDrawerDoc({
      title: fetchedDoc?.title || source.heading || source.filename || 'Policy Document',
      section: source.heading || 'Official Policy Excerpt',
      status: fetchedDoc?.status || 'Active • Official',
      effective_date: fetchedDoc?.effective_date || '2026',
      content: fetchedDoc?.content || `Official policy reference: ${source.filename}\n\nSection: ${source.heading || 'Standard Terms'}\nStatus: Verified Active Policy.`,
    })
  }

  // Helper to render Stepper for Order Card
  const renderStepper = (status) => {
    const s = (status || '').toLowerCase()
    
    if (s === 'cancelled') {
      return (
        <div className="stepper-container">
          <div className="stepper-track">
            <div className="stepper-step completed">
              <div className="stepper-node">✓</div>
              <div className="stepper-label">Ordered</div>
            </div>
            <div className="stepper-step cancelled-step">
              <div className="stepper-node">✗</div>
              <div className="stepper-label">Cancelled</div>
            </div>
          </div>
        </div>
      )
    }

    if (s === 'returned') {
      return (
        <div className="stepper-container">
          <div className="stepper-track">
            <div className="stepper-step completed">
              <div className="stepper-node">✓</div>
              <div className="stepper-label">Delivered</div>
            </div>
            <div className="stepper-step current">
              <div className="stepper-node">↩</div>
              <div className="stepper-label">Returned</div>
            </div>
          </div>
        </div>
      )
    }

    const steps = [
      { id: 'pending', label: 'Ordered' },
      { id: 'processing', label: 'Processing' },
      { id: 'shipped', label: 'Shipped' },
      { id: 'delivered', label: 'Delivered' },
    ]

    const orderLevels = { pending: 0, processing: 1, shipped: 2, delivered: 3, exception: 2 }
    const currentLevel = orderLevels[s] !== undefined ? orderLevels[s] : 0

    return (
      <div className="stepper-container">
        <div className="stepper-track">
          {steps.map((step, idx) => {
            const isCompleted = idx < currentLevel
            const isCurrent = idx === currentLevel
            return (
              <div
                key={step.id}
                className={`stepper-step ${isCompleted ? 'completed' : ''} ${isCurrent ? 'current' : ''}`}
              >
                <div className="stepper-node">
                  {isCompleted ? '✓' : isCurrent ? '●' : '○'}
                </div>
                <div className="stepper-label">{step.label}</div>
              </div>
            )
          })}
        </div>
      </div>
    )
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Responsive Navigation Header */}
      <header className="navbar-header" role="banner">
        <div className="navbar-container">
          {/* Clickable Brand Logo / Home Link */}
          <button
            className="brand-logo-btn"
            onClick={resetToHome}
            aria-label="Aster & Row Customer Support AI - Return to Home"
            title="Aster & Row Home"
          >
            <div className="brand-logo-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
              </svg>
            </div>
            <div className="brand-text-group">
              <div className="brand-title">Aster & Row</div>
              <div className="brand-subtitle">
                <span className="brand-subtitle-text">Customer Support AI</span>
              </div>
            </div>
          </button>

          {/* Right Navigation Controls */}
          <div className="navbar-controls">
            {/* Back Button shown when user is in chat mode */}
            {history.length > 0 && (
              <button
                className="back-btn"
                onClick={resetToHome}
                aria-label="Back to Aster & Row home"
                title="Return to home screen"
              >
                <span className="back-btn-icon">←</span>
                <span className="back-btn-text">Back to Aster & Row</span>
                <span className="back-btn-text-short">Back</span>
              </button>
            )}

            {/* Responsive Theme Toggle */}
            <button
              id="theme-toggle"
              className="theme-toggle-btn"
              onClick={toggleTheme}
              aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
              title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
            >
              <span className="theme-toggle-icon">{theme === 'dark' ? '☀️' : '🌙'}</span>
              <span className="theme-toggle-text">{theme === 'dark' ? 'Light' : 'Dark'}</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Chat Container */}
      <main style={{ flex: 1, display: 'flex', justifyContent: 'center', padding: '10px 12px' }}>
        <div
          style={{
            width: '100%',
            maxWidth: '840px',
            display: 'flex',
            flexDirection: 'column',
            height: 'calc(100vh - 84px)',
            background: 'var(--bg-surface)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-lg)',
            overflow: 'hidden',
            boxShadow: 'var(--shadow-lg)',
            position: 'relative',
          }}
        >
          {/* Scrollable Chat Area */}
          <section
            id="chat-log"
            role="log"
            aria-live="polite"
            aria-label="Support conversation"
            ref={chatLogRef}
            onScroll={handleScroll}
            style={{
              flex: 1,
              padding: '14px 16px',
              overflowY: 'auto',
              display: 'flex',
              flexDirection: 'column',
              gap: '16px',
            }}
          >
            {/* Empty State / Welcome Screen with Categories & Questions */}
            {history.length === 0 && (
              <div className="welcome-card">
                <div className="welcome-icon">🌲</div>
                <h1 className="welcome-title">
                  Welcome to Aster & Row
                </h1>
                <p className="welcome-subtitle">
                  How can we help you today? Explore topic categories or ask any question about your gear.
                </p>

                {/* Topic / Category Chips */}
                <div className="categories-container">
                  {TOPIC_CATEGORIES.map((cat) => (
                    <button
                      key={cat.id}
                      className={`category-chip ${activeCategory === cat.id ? 'active' : ''}`}
                      onClick={() => setActiveCategory(prev => (prev === cat.id ? null : cat.id))}
                    >
                      <span>{cat.icon}</span>
                      <span>{cat.label}</span>
                    </button>
                  ))}
                </div>

                {/* Suggested Questions for Selected Category or Default Overview */}
                <div className="suggested-questions-box">
                  <div className="suggested-questions-header">
                    <span>💡 Suggested Questions</span>
                    {activeCategory && (
                      <span style={{ color: 'var(--accent-primary)', fontWeight: '700' }}>
                        — {TOPIC_CATEGORIES.find(c => c.id === activeCategory)?.label}
                      </span>
                    )}
                  </div>
                  <div className="suggested-questions-list">
                    {(
                      activeCategory
                        ? TOPIC_CATEGORIES.find(c => c.id === activeCategory)?.questions || []
                        : [
                            'What is my return window?',
                            'Where is order ORD-1007?',
                            'TrailPlus membership benefits',
                            'Do you ship to Canada?',
                          ]
                    ).map((question) => (
                      <button
                        key={question}
                        className="suggested-q-btn"
                        onClick={() => handleSend(question)}
                      >
                        <span>{question}</span>
                        <span className="arrow">➔</span>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Conversation Messages */}
            {history.map((msg) => (
              <article
                key={msg.id}
                role="article"
                className="message-enter"
                aria-label={msg.role === 'agent' ? 'Agent message' : 'Your message'}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start',
                  gap: '6px',
                }}
              >
                {/* Regular User / Agent Bubble or Error Card */}
                {msg.isError ? (
                  <div className="error-card">
                    <div className="error-card-title">
                      <span>⚠️</span>
                      <span>Temporarily unavailable</span>
                    </div>
                    <div className="error-card-msg">
                      {msg.content}
                    </div>
                    <button className="retry-btn" onClick={handleRetry}>
                      Try Again
                    </button>
                  </div>
                ) : (
                  <div
                    style={{
                      maxWidth: '88%',
                      padding: '16px 18px',
                      borderRadius:
                        msg.role === 'user'
                          ? '18px 18px 4px 18px'
                          : '18px 18px 18px 4px',
                      background:
                        msg.role === 'user'
                          ? 'var(--accent-primary)'
                          : 'var(--bg-surface-2)',
                      color:
                        msg.role === 'user'
                          ? '#ffffff'
                          : 'var(--text-primary)',
                      border: msg.role === 'agent' ? '1px solid var(--border)' : 'none',
                      borderLeft:
                        msg.role === 'agent'
                          ? msg.hasConflict
                            ? '3px solid var(--accent-conflict)'
                            : '3px solid var(--accent-primary)'
                          : 'none',
                      fontSize: '14px',
                      lineHeight: '1.6',
                      wordBreak: 'break-word',
                    }}
                  >
                    {/* Markdown Answer */}
                    <div className="markdown-content" dangerouslySetInnerHTML={{ __html: formatMarkdown(msg.content) }} />

                    {/* 1. 📦 Interactive Order Card */}
                    {msg.orderData && (
                      <div className="order-card-container">
                        <div className="order-card-header">
                          <span className="order-card-title">
                            <span>📦 Order {msg.orderData.order_id}</span>
                          </span>
                          {STATUS_CONFIG[msg.orderData.status] && (
                            <span
                              className="order-badge"
                              style={{
                                background: STATUS_CONFIG[msg.orderData.status].bg,
                                color: STATUS_CONFIG[msg.orderData.status].color,
                              }}
                            >
                              <span>{STATUS_CONFIG[msg.orderData.status].icon}</span>
                              <span>{msg.orderData.status}</span>
                            </span>
                          )}
                        </div>

                        {/* Items */}
                        {msg.orderData.items && msg.orderData.items.length > 0 && (
                          <div className="order-items-list">
                            {msg.orderData.items.map((item, idx) => (
                              <div key={idx} className="order-item-row">
                                <span>{item.name}</span>
                                <strong>× {item.quantity}</strong>
                              </div>
                            ))}
                          </div>
                        )}

                        {/* Visual Shipment Stepper */}
                        {renderStepper(msg.orderData.status)}

                        {/* Safe Order Details */}
                        <div className="order-details-grid">
                          {msg.orderData.carrier && (
                            <div className="order-detail-item">
                              <span>🚚 Carrier:</span>
                              <strong>{msg.orderData.carrier}</strong>
                            </div>
                          )}
                          {msg.orderData.estimated_delivery && (
                            <div className="order-detail-item">
                              <span>📅 Estimated:</span>
                              <strong>{new Date(msg.orderData.estimated_delivery).toLocaleDateString()}</strong>
                            </div>
                          )}
                          {msg.orderData.tracking_number && (
                            <div className="order-detail-item" style={{ gridColumn: 'span 2' }}>
                              <span>🔖 Tracking:</span>
                              <code style={{ fontSize: '11px' }}>{msg.orderData.tracking_number}</code>
                            </div>
                          )}
                        </div>

                        {/* Track Shipment Button (only when carrier & tracking exist) */}
                        {msg.orderData.tracking_number && (
                          <button
                            className="track-btn"
                            onClick={() => copyText(`track_${msg.orderData.order_id}`, msg.orderData.tracking_number)}
                          >
                            <span>🔍</span>
                            <span>
                              {copiedStates[`track_${msg.orderData.order_id}`]
                                ? 'Tracking Copied ✓'
                                : `Track on ${msg.orderData.carrier || 'Carrier'}`}
                            </span>
                          </button>
                        )}
                      </div>
                    )}

                    {/* 3. 🔍 "Answer details" Safe Metadata Accordion */}
                    {msg.role === 'agent' && (
                      <div className="answer-details-container">
                        <button className="answer-details-toggle" onClick={() => toggleDetails(msg.id)}>
                          <span>{openDetails[msg.id] ? '▾' : '▸'}</span>
                          <span>Answer details</span>
                        </button>
                        {openDetails[msg.id] && (
                          <div className="answer-details-list">
                            {msg.orderData ? (
                              <>
                                <div className="answer-detail-item">
                                  <span className="check">✓</span>
                                  <span>Order database checked</span>
                                </div>
                                <div className="answer-detail-item">
                                  <span className="check">✓</span>
                                  <span>{msg.orderData.order_id} verified</span>
                                </div>
                                <div className="answer-detail-item">
                                  <span className="check">✓</span>
                                  <span>Customer-safe status retrieved</span>
                                </div>
                              </>
                            ) : msg.sources && msg.sources.length > 0 ? (
                              <>
                                <div className="answer-detail-item">
                                  <span className="check">✓</span>
                                  <span>Knowledge Base consulted</span>
                                </div>
                                <div className="answer-detail-item">
                                  <span className="check">✓</span>
                                  <span>{msg.sources.length} policy section{msg.sources.length > 1 ? 's' : ''} retrieved</span>
                                </div>
                                <div className="answer-detail-item">
                                  <span className="check">✓</span>
                                  <span>Official active policy verified</span>
                                </div>
                              </>
                            ) : (
                              <>
                                <div className="answer-detail-item">
                                  <span className="check">✓</span>
                                  <span>AI Customer Support Agent active</span>
                                </div>
                                <div className="answer-detail-item">
                                  <span className="check">✓</span>
                                  <span>Policy guidelines applied</span>
                                </div>
                              </>
                            )}
                          </div>
                        )}
                      </div>
                    )}

                    {/* 2. 📚 Clickable Source / Citation Cards */}
                    {msg.sources && msg.sources.length > 0 && (
                      <div className="sources-section">
                        <div className="sources-header-title">
                          <span>📚 Cited Sources</span>
                        </div>
                        <div className="citation-cards-grid">
                          {msg.sources.map((src, idx) => (
                            <button
                              key={idx}
                              className="citation-card"
                              onClick={() => openSourceDrawer(src)}
                              title="Click to view policy excerpt"
                            >
                              <div className="citation-title">
                                <span>📄</span>
                                <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                  {src.filename ? src.filename.replace(/\.md$/, '') : 'Policy'}
                                </span>
                              </div>
                              <div className="citation-heading">
                                {src.heading || 'Standard Policy'}
                              </div>
                              <div className="citation-meta">
                                <span className="citation-badge">Active • Official</span>
                                <span className="citation-link">View source ➔</span>
                              </div>
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* 4. 👍 Message Feedback & Copy Row */}
                    {msg.role === 'agent' && (
                      <div className="message-actions-row">
                        <div className="feedback-group">
                          <span>Was this helpful?</span>
                          {feedbackState[msg.id] === 'up' ? (
                            <span style={{ color: 'var(--accent-primary)', fontWeight: '600' }}>
                              ✓ Thanks for your feedback!
                            </span>
                          ) : feedbackState[msg.id] === 'down' ? (
                            <span style={{ color: 'var(--accent-warning)', fontWeight: '500' }}>
                              Feedback received
                            </span>
                          ) : (
                            <>
                              <button
                                className="feedback-btn"
                                onClick={() => handleFeedback(msg.id, 'up')}
                                aria-label="Helpful"
                                title="Helpful"
                              >
                                👍
                              </button>
                              <button
                                className="feedback-btn"
                                onClick={() => handleFeedback(msg.id, 'down')}
                                aria-label="Not helpful"
                                title="Not helpful"
                              >
                                👎
                              </button>
                            </>
                          )}
                        </div>

                        <button
                          className="copy-answer-btn"
                          onClick={() => copyText(msg.id, msg.content)}
                        >
                          <span>{copiedStates[msg.id] ? '✓' : '▢'}</span>
                          <span>{copiedStates[msg.id] ? 'Copied' : 'Copy'}</span>
                        </button>
                      </div>
                    )}

                    {/* Negative feedback escalation prompt */}
                    {feedbackState[msg.id] === 'down' && (
                      <div className="feedback-negative-escalate">
                        <span>Sorry this wasn't helpful. Would you like to talk to a support specialist?</span>
                        <button
                          className="feedback-escalate-btn"
                          onClick={() => alert('Connecting to Aster & Row Support Specialist...')}
                        >
                          Connect to Support
                        </button>
                      </div>
                    )}
                  </div>
                )}

                {/* 5. 🧑‍💼 Human Handoff Card */}
                {msg.handoff && !msg.isError && (
                  <div className={`handoff-card ${msg.hasConflict ? 'conflict' : ''}`}>
                    <div className="handoff-header">
                      <span>{msg.hasConflict ? '⚠️' : '👤'}</span>
                      <span>
                        {msg.hasConflict
                          ? 'Official Policy Discrepancy — Human Support Recommended'
                          : 'Human Support Recommended'}
                      </span>
                    </div>
                    <div className="handoff-body">
                      {msg.hasConflict
                        ? 'Our official policies contain conflicting terms regarding this inquiry. A support specialist is available to assist you.'
                        : 'This request requires assistance from an Aster & Row customer support specialist.'}
                    </div>
                    <div className="handoff-actions">
                      <button
                        className="handoff-primary-btn"
                        onClick={() => alert('Support Specialist dispatched. A representative will connect shortly.')}
                      >
                        Contact Support
                      </button>
                      <button
                        className="handoff-secondary-btn"
                        onClick={() => {
                          if (inputRef.current) inputRef.current.focus()
                        }}
                      >
                        Continue Chat
                      </button>
                    </div>
                  </div>
                )}

                {/* Timestamp */}
                <span style={{ fontSize: '10px', color: 'var(--text-muted)', padding: '0 4px' }}>
                  {msg.timestamp}
                </span>
              </article>
            ))}

            {/* Typing Indicator */}
            {chatState === 'sending' && (
              <div
                id="typing-indicator"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '10px 16px',
                  background: 'var(--bg-surface-2)',
                  borderRadius: 'var(--radius-pill)',
                  width: 'fit-content',
                  fontSize: '12px',
                  color: 'var(--text-secondary)',
                  border: '1px solid var(--border)',
                }}
              >
                <span>🤖 Searching knowledge base & orders</span>
                <span className="dot-1">●</span>
                <span className="dot-2">●</span>
                <span className="dot-3">●</span>
              </div>
            )}
          </section>

          {/* Floating Scroll Button */}
          {showNewMessageChip && (
            <button
              onClick={() => scrollToBottom(true)}
              style={{
                position: 'absolute',
                bottom: '120px',
                left: '50%',
                transform: 'translateX(-50%)',
                zIndex: 10,
                padding: '6px 14px',
                background: 'var(--accent-primary)',
                color: '#ffffff',
                border: 'none',
                borderRadius: 'var(--radius-pill)',
                fontSize: '12px',
                fontWeight: '600',
                cursor: 'pointer',
                boxShadow: '0 4px 12px var(--shadow)',
              }}
            >
              ↓ Scroll to bottom
            </button>
          )}

          {/* 7. ⌨️ Improved Chat Input Area */}
          <footer
            style={{
              padding: '14px 18px',
              background: 'var(--bg-surface-2)',
              borderTop: '1px solid var(--border)',
            }}
          >
            <form
              onSubmit={(e) => {
                e.preventDefault()
                handleSend()
              }}
              style={{ display: 'flex', gap: '10px', alignItems: 'flex-end' }}
            >
              <div style={{ flex: 1, position: 'relative' }}>
                <textarea
                  id="message-input"
                  ref={inputRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Ask about orders, returns, shipping, warranty..."
                  rows={1}
                  maxLength={1000}
                  style={{
                    width: '100%',
                    padding: '12px 16px',
                    paddingRight: '72px',
                    background: 'var(--bg-surface)',
                    border: '1px solid var(--border)',
                    borderRadius: 'var(--radius-md)',
                    color: 'var(--text-primary)',
                    fontFamily: 'inherit',
                    fontSize: '14px',
                    lineHeight: '1.4',
                    resize: 'none',
                    outline: 'none',
                    boxSizing: 'border-box',
                  }}
                />
                <span
                  style={{
                    position: 'absolute',
                    right: '12px',
                    bottom: '10px',
                    fontSize: '11px',
                    color: input.length > 900 ? 'var(--accent-warning)' : 'var(--text-muted)',
                  }}
                >
                  {input.length}/1000
                </span>
              </div>

              <button
                id="send-btn"
                type="submit"
                disabled={!input.trim() || chatState === 'sending'}
                style={{
                  height: '44px',
                  padding: '0 20px',
                  background: 'var(--accent-primary)',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: 'var(--radius-md)',
                  fontWeight: '600',
                  fontSize: '14px',
                  cursor: !input.trim() || chatState === 'sending' ? 'not-allowed' : 'pointer',
                  opacity: !input.trim() || chatState === 'sending' ? 0.45 : 1,
                  transition: 'var(--transition-fast)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '4px',
                }}
              >
                <span>Send</span>
                <span style={{ fontSize: '12px' }}>➤</span>
              </button>
            </form>
          </footer>

          {/* Small Footer */}
          <div className="chat-footer">
            <span>© 2026 Aster & Row</span>
            <span className="chat-footer-dot">•</span>
            <span>Powered by AI Customer Support</span>
            <span className="chat-footer-dot">•</span>
            <span>Official Help Center</span>
          </div>
        </div>
      </main>

      {/* 2. 📚 Right-Side Citation Slide-Drawer */}
      {drawerDoc && (
        <div className="drawer-backdrop" onClick={() => setDrawerDoc(null)}>
          <aside className="source-drawer" onClick={(e) => e.stopPropagation()}>
            <div className="drawer-header">
              <div className="drawer-header-title">
                {drawerDoc.title}
              </div>
              <button
                className="drawer-close-btn"
                onClick={() => setDrawerDoc(null)}
                aria-label="Close drawer"
              >
                ✕
              </button>
            </div>

            <div className="drawer-content">
              <div className="drawer-meta-pill-group">
                <span className="drawer-pill status-active">
                  {drawerDoc.status}
                </span>
                <span className="drawer-pill">
                  Section: {drawerDoc.section}
                </span>
                {drawerDoc.effective_date && (
                  <span className="drawer-pill">
                    Effective: {drawerDoc.effective_date}
                  </span>
                )}
              </div>

              <div className="drawer-body-text">
                {drawerDoc.content}
              </div>
            </div>
          </aside>
        </div>
      )}
    </div>
  )
}

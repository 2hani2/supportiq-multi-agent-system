import { useState, useEffect, useRef } from "react";
import {
  Bot,
  User,
  Send,
  Package,
  RotateCcw,
  Truck,
  Headset,
  Sparkles,
  Plus,
  MessageSquare,
  Trash2,
  Clock3,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import "./App.css";

const API_URL = "http://localhost:8000/agent/support";
const STORAGE_KEY = "supportiq_conversations_v1";

const suggestions = [
  { icon: Package, title: "Track my order", prompt: "What is the status of order TRK1001?" },
  { icon: RotateCcw, title: "Refund policy", prompt: "What is your refund policy?" },
  { icon: Truck, title: "Shipping information", prompt: "How long does standard delivery take?" },
  { icon: Headset, title: "Support tickets", prompt: "Does Aarav Sharma have any open support tickets?" },
];

function makeConversation() {
  return {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    title: "New conversation",
    messages: [],
    updatedAt: new Date().toISOString(),
  };
}

function makeTitle(text) {
  const cleaned = text.replace(/\s+/g, " ").trim();
  return cleaned.length > 34 ? `${cleaned.slice(0, 34).trim()}…` : cleaned || "New conversation";
}

function formatTimestamp(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleDateString([], { month: "short", day: "numeric" });
}

function App() {
  const [conversations, setConversations] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      const parsed = saved ? JSON.parse(saved) : [];
      return Array.isArray(parsed) ? parsed : [];
    } catch (error) {
      console.warn("Could not load saved conversations:", error);
      return [];
    }
  });
  const [activeConversationId, setActiveConversationId] = useState(() => {
    try {
      const saved = localStorage.getItem(`${STORAGE_KEY}_active`);
      return saved || null;
    } catch {
      return null;
    }
  });
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const messagesEndRef = useRef(null);

  const activeConversation = conversations.find((item) => item.id === activeConversationId) || null;
  const messages = activeConversation?.messages || [];

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations));
    } catch (error) {
      console.warn("Could not save conversations:", error);
    }
  }, [conversations]);

  useEffect(() => {
    try {
      if (activeConversationId) localStorage.setItem(`${STORAGE_KEY}_active`, activeConversationId);
      else localStorage.removeItem(`${STORAGE_KEY}_active`);
    } catch (error) {
      console.warn("Could not save active conversation:", error);
    }
  }, [activeConversationId]);

  useEffect(() => {
    if (activeConversationId && !conversations.some((item) => item.id === activeConversationId)) {
      setActiveConversationId(conversations[0]?.id || null);
    }
  }, [conversations, activeConversationId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, loading]);

  function updateConversation(id, updater) {
    setConversations((previous) =>
      previous.map((conversation) =>
        conversation.id === id
          ? { ...updater(conversation), updatedAt: new Date().toISOString() }
          : conversation,
      ),
    );
  }

  function startNewChat() {
    const conversation = makeConversation();
    setConversations((previous) => [conversation, ...previous]);
    setActiveConversationId(conversation.id);
    setQuestion("");
    setError("");
  }

  function selectConversation(id) {
    setActiveConversationId(id);
    setQuestion("");
    setError("");
  }

  function deleteConversation(event, id) {
    event.stopPropagation();
    const remaining = conversations.filter((item) => item.id !== id);
    setConversations(remaining);
    if (activeConversationId === id) {
      setActiveConversationId(remaining[0]?.id || null);
    }
    setError("");
  }

  async function sendMessage(text = question) {
    const trimmed = text.trim();
    if (!trimmed || loading) return;

    let conversationId = activeConversationId;
    if (!conversationId) {
      const newConversation = makeConversation();
      conversationId = newConversation.id;
      setConversations((previous) => [newConversation, ...previous]);
      setActiveConversationId(conversationId);
    }

    updateConversation(conversationId, (conversation) => ({
      ...conversation,
      title: conversation.messages.length === 0 ? makeTitle(trimmed) : conversation.title,
      messages: [...conversation.messages, { role: "user", content: trimmed, createdAt: new Date().toISOString() }],
    }));
    setQuestion("");
    setError("");
    setLoading(true);

    try {
      const response = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: trimmed }),
      });
      const responseText = await response.text();
      let data = {};
      try {
        data = responseText ? JSON.parse(responseText) : {};
      } catch {
        throw new Error(`The API returned an invalid response (HTTP ${response.status}).`);
      }
      if (!response.ok) throw new Error(data.detail || `API request failed with HTTP ${response.status}.`);
      if (typeof data.answer !== "string" || !data.answer.trim()) {
        throw new Error("The API responded, but no answer was returned. Check the backend response.");
      }
      updateConversation(conversationId, (conversation) => ({
        ...conversation,
        messages: [...conversation.messages, {
          role: "assistant",
          content: data.answer,
          agent: data.selected_agent,
          createdAt: new Date().toISOString(),
        }],
      }));
    } catch (err) {
      console.error("Support API request failed:", err);
      let message = err.message || "An unexpected error occurred.";
      if (err instanceof TypeError || message.toLowerCase().includes("failed to fetch")) {
        message = "Cannot reach the support API. Check that Docker is running and http://localhost:8000/docs opens. If it does, check the browser Console for a CORS error.";
      }
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon"><Bot size={23} /></div>
          <div><strong>SupportIQ</strong><span>AI CUSTOMER CARE</span></div>
        </div>

        <button className="new-chat" onClick={startNewChat}>
          <Plus size={18} /> New conversation
        </button>

        <div className="sidebar-label">YOUR ASSISTANT</div>
        <div className="sidebar-info">
          <Sparkles size={17} />
          <div><strong>AI Support Assistant</strong><span>Orders, shipping &amp; policies</span></div>
        </div>

        <div className="history-heading">
          <span className="sidebar-label">RECENT CONVERSATIONS</span>
          <MessageSquare size={14} />
        </div>
        <div className="conversation-list">
          {conversations.length === 0 ? (
            <p className="history-empty">Your chats will appear here.</p>
          ) : conversations.slice().sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt)).map((conversation) => (
            <button
              key={conversation.id}
              className={`conversation-item ${conversation.id === activeConversationId ? "active" : ""}`}
              onClick={() => selectConversation(conversation.id)}
              title={conversation.title}
            >
              <MessageSquare size={15} className="conversation-icon" />
              <span className="conversation-details">
                <span className="conversation-title">{conversation.title || "New conversation"}</span>
                <span className="conversation-date"><Clock3 size={11} /> {formatTimestamp(conversation.updatedAt)}</span>
              </span>
              <span
                className="delete-conversation"
                role="button"
                tabIndex={0}
                aria-label={`Delete ${conversation.title}`}
                title="Delete conversation"
                onClick={(event) => deleteConversation(event, conversation.id)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") deleteConversation(event, conversation.id);
                }}
              ><Trash2 size={14} /></span>
            </button>
          ))}
        </div>

        <div className="sidebar-footer"><span className="status-dot" /><span>Support system online</span></div>
      </aside>

      <main className="main-panel">
        <header className="topbar">
          <div><div className="page-eyebrow">CUSTOMER SERVICE</div><h1>How can we help?</h1></div>
          <div className="online-badge"><span className="status-dot" /> AI assistant</div>
        </header>

        <section className="chat-area">
          {messages.length === 0 ? (
            <div className="welcome">
              <div className="welcome-icon"><Sparkles size={27} /></div>
              <h2>Your support, simplified.</h2>
              <p>Ask about an order, shipping timelines, returns, or your support tickets. I'll help you find the answer.</p>
              <div className="suggestions">
                {suggestions.map((item) => {
                  const Icon = item.icon;
                  return (
                    <button className="suggestion-card" key={item.title} onClick={() => sendMessage(item.prompt)} disabled={loading}>
                      <Icon size={20} /><span>{item.title}</span><span className="suggestion-arrow">↗</span>
                    </button>
                  );
                })}
              </div>
            </div>
          ) : (
            <div className="messages">
              {messages.map((message, index) => (
                <article className={`message ${message.role}`} key={`${activeConversationId}-${message.role}-${index}`}>
                  <div className="message-avatar">{message.role === "assistant" ? <Bot size={18} /> : <User size={18} />}</div>
                  <div className="message-body">
                    <div className="message-name">{message.role === "assistant" ? "SupportIQ" : "You"}</div>
                    <div className="message-content">
                      {message.role === "assistant" ? (
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content.replace(/\\\s*\n/g, "\n").replace(/\\/g, "\n")}</ReactMarkdown>
                      ) : message.content}
                    </div>
                    {message.agent && <span className="agent-tag">Handled by {message.agent} agent</span>}
                  </div>
                </article>
              ))}
              {loading && <div className="message assistant"><div className="message-avatar"><Bot size={18} /></div><div className="message-body"><div className="message-name">SupportIQ</div><div className="typing"><span /><span /><span /><small>Finding the right answer…</small></div></div></div>}
              <div className="messages-end" ref={messagesEndRef} />
            </div>
          )}
        </section>

        {error && <div className="error-message" role="alert"><strong>Request failed:</strong> {error}</div>}
        <form className="composer" onSubmit={(event) => { event.preventDefault(); sendMessage(); }}>
          <input value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Ask anything about your order or support…" aria-label="Your support question" disabled={loading} />
          <button className="send-button" type="submit" disabled={loading || !question.trim()} aria-label="Send message"><Send size={18} /></button>
        </form>
        <p className="disclaimer">AI-generated responses may need verification. Avoid entering passwords or payment details.</p>
      </main>
    </div>
  );
}

export default App;

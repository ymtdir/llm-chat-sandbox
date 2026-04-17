import { useState, useEffect, useRef, FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../api/client';
import type { Message } from '../types/diary';
import './Chat.css';

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage: Message = {
      role: 'user',
      content: input.trim(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await apiClient.chat([...messages, userMessage]);
      const assistantMessage: Message = {
        role: 'assistant',
        content: response.response,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      console.error('Chat error:', err);
      const errorMessage: Message = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    apiClient.logout();
  };

  return (
    <div className="chat-page">
      <header className="chat-header">
        <div className="container">
          <h2>AI Diary Companion</h2>
          <div className="header-actions">
            <button
              onClick={() => navigate('/diaries')}
              className="button-primary"
            >
              My Diaries
            </button>
            <button onClick={handleLogout} className="button-dark">
              Sign Out
            </button>
          </div>
        </div>
      </header>

      <main className="chat-main">
        <div className="container">
          <div className="chat-messages">
            {messages.length === 0 && (
              <div className="chat-empty">
                <h3>Start a conversation</h3>
                <p>
                  Share your thoughts, and I'll help create your diary entry.
                </p>
              </div>
            )}

            {messages.map((message, index) => (
              <div
                key={index}
                className={`chat-message chat-message-${message.role}`}
              >
                <div className="chat-message-content">{message.content}</div>
              </div>
            ))}

            {loading && (
              <div className="chat-message chat-message-assistant">
                <div className="chat-message-content chat-loading">
                  Thinking...
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>
      </main>

      <footer className="chat-footer">
        <div className="container">
          <form onSubmit={handleSubmit} className="chat-input-form">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Tell me about your day..."
              className="chat-input"
              disabled={loading}
            />
            <button
              type="submit"
              className="button-primary"
              disabled={loading || !input.trim()}
            >
              Send
            </button>
          </form>
        </div>
      </footer>
    </div>
  );
}

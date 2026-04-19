import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../api/client';
import type { Message, WebSocketMessage } from '../types/diary';
import MessageList from '../components/MessageList';
import MessageInput from '../components/MessageInput';
import './Chat.css';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
const DEFAULT_CHARACTER_ID = 1;

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [ws, setWs] = useState<WebSocket | null>(null);
  const navigate = useNavigate();

  // Initialize conversation and WebSocket
  useEffect(() => {
    let websocket: WebSocket | null = null;

    const initializeChat = async () => {
      try {
        // Get or create conversation
        const { id } =
          await apiClient.getOrCreateConversation(DEFAULT_CHARACTER_ID);
        setConversationId(id);

        // Load message history
        const history = await apiClient.getMessages(id);
        setMessages(history);

        // Setup WebSocket connection
        const token = localStorage.getItem('access_token');
        if (token) {
          // TODO: Get actual user_id from auth token
          const userId = 1; // Placeholder
          websocket = new WebSocket(`${WS_URL}/ws/${userId}?token=${token}`);

          websocket.onopen = () => {
            console.log('WebSocket connected');
          };

          websocket.onmessage = (event) => {
            const wsMessage: WebSocketMessage = JSON.parse(event.data);

            if (wsMessage.type === 'message:new' && wsMessage.data) {
              setMessages((prev) => [
                ...prev,
                {
                  role: wsMessage.data!.role,
                  content: wsMessage.data!.content,
                  timestamp:
                    wsMessage.data!.timestamp || new Date().toISOString(),
                },
              ]);
              setIsTyping(false);
            } else if (wsMessage.type === 'message:typing') {
              setIsTyping(true);
            }
          };

          websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
          };

          websocket.onclose = () => {
            console.log('WebSocket disconnected');
          };

          setWs(websocket);
        }
      } catch (err) {
        console.error('Failed to initialize chat:', err);
      }
    };

    initializeChat();

    // Cleanup WebSocket on unmount
    return () => {
      if (websocket) {
        websocket.close();
      }
    };
  }, []);

  const handleSendMessage = async (content: string) => {
    if (!conversationId || loading) return;

    const userMessage: Message = {
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    try {
      await apiClient.sendMessage(conversationId, content);
      // AI response will come via WebSocket
    } catch (err) {
      console.error('Send message error:', err);
      const errorMessage: Message = {
        role: 'assistant',
        content:
          '申し訳ございません。エラーが発生しました。もう一度お試しください。',
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
      setIsTyping(false);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    if (ws) {
      ws.close();
    }
    apiClient.logout();
  };

  return (
    <div className="chat-page">
      <header className="chat-header">
        <div className="container">
          <h2>AI日記コンパニオン</h2>
          <div className="header-actions">
            <button
              onClick={() => navigate('/diaries')}
              className="button-primary"
            >
              日記一覧
            </button>
            <button onClick={handleLogout} className="button-dark">
              ログアウト
            </button>
          </div>
        </div>
      </header>

      <main className="chat-main">
        <div className="container">
          <MessageList messages={messages} isTyping={isTyping} />
        </div>
      </main>

      <footer className="chat-footer">
        <div className="container">
          <MessageInput onSend={handleSendMessage} disabled={loading} />
        </div>
      </footer>
    </div>
  );
}

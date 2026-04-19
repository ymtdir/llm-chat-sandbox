import { useEffect, useRef } from 'react';
import MessageBubble from './MessageBubble';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

interface MessageListProps {
  messages: Message[];
  isTyping?: boolean;
}

export default function MessageList({ messages, isTyping }: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  return (
    <div className="message-list">
      {messages.length === 0 && (
        <div className="message-list-empty">
          <h3>会話を始めましょう</h3>
          <p>あなたの思いを共有してください。日記の作成をお手伝いします。</p>
        </div>
      )}

      {messages.map((message, index) => (
        <MessageBubble
          key={index}
          role={message.role}
          content={message.content}
          timestamp={message.timestamp}
        />
      ))}

      {isTyping && (
        <div className="message-bubble message-bubble-assistant">
          <div className="message-content typing-indicator">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
      )}

      <div ref={messagesEndRef} />
    </div>
  );
}

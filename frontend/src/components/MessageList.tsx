import { Message } from '../types';

interface MessageListProps {
  messages: Message[];
  isLoading: boolean;
}

const MessageList = ({ messages, isLoading }: MessageListProps) => {
  return (
    <div className="chat-container">
      {messages.map((message, index) => (
        <div key={index} className={`message ${message.role}`}>
          <div className="message-avatar">{message.role === 'user' ? 'U' : 'AI'}</div>
          <div className="message-content">
            <div className="message-bubble">{message.content}</div>
            {message.timestamp && (
              <div className="message-metadata">
                <span>{new Date(message.timestamp).toLocaleTimeString()}</span>
              </div>
            )}
          </div>
        </div>
      ))}
      {isLoading && (
        <div className="message assistant">
          <div className="message-avatar">AI</div>
          <div className="message-content">
            <div className="message-bubble">
              <div className="typing-indicator">
                <span className="typing-dot"></span>
                <span className="typing-dot"></span>
                <span className="typing-dot"></span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MessageList;

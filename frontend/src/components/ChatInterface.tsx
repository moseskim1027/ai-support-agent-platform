import { useState, useEffect, useRef } from 'react';
import { apiService } from '../services/api';
import { Message, ChatResponse } from '../types';
import MessageList from './MessageList';
import ChatInput from './ChatInput';
import WelcomeScreen from './WelcomeScreen';

const ChatInterface = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Track if we're in chat mode for browser history
  const [inChatMode, setInChatMode] = useState(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Handle browser back button
  useEffect(() => {
    const handlePopState = () => {
      if (inChatMode) {
        handleBackToWelcome();
      }
    };

    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, [inChatMode]);

  // Push history state when entering chat mode
  useEffect(() => {
    if (messages.length > 0 && !inChatMode) {
      setInChatMode(true);
      window.history.pushState({ chat: true }, '', '');
    }
  }, [messages.length]);

  const handleBackToWelcome = () => {
    setMessages([]);
    setConversationId(null);
    setError(null);
    setInChatMode(false);
  };

  const handleSendMessage = async (content: string) => {
    if (!content.trim()) return;

    const userMessage: Message = {
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    try {
      const response: ChatResponse = await apiService.sendMessage({
        message: content,
        conversation_id: conversationId || undefined,
        history: messages,
      });

      if (!conversationId) {
        setConversationId(response.conversation_id);
      }

      const assistantMessage: Message = {
        role: 'assistant',
        content: response.message,
        timestamp: response.metadata?.timestamp,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      setError('Failed to send message. Please try again.');
      console.error('Error sending message:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSamplePrompt = (prompt: string) => {
    handleSendMessage(prompt);
  };

  return (
    <>
      {messages.length === 0 ? (
        <WelcomeScreen onSamplePrompt={handleSamplePrompt} />
      ) : (
        <>
          <button
            className="back-button"
            onClick={() => {
              handleBackToWelcome();
              window.history.back();
            }}
            aria-label="Back to welcome screen"
          >
            ← Back
          </button>
          <MessageList messages={messages} isLoading={isLoading} />
        </>
      )}
      {error && <div className="error-message">{error}</div>}
      <div ref={messagesEndRef} />
      <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} disabled={isLoading} />
    </>
  );
};

export default ChatInterface;

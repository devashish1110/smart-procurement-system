import { useState, useEffect, useRef } from 'react';
import { chatbotAPI } from '../services/api';
import { Send, Bot, User, Loader } from 'lucide-react';
import { formatDateTime } from '../utils/helpers';

const Chatbot = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    // Initial greeting
    setMessages([{
      role: 'assistant',
      content: 'Hello! I\'m your AI assistant for the Smart Procurement System. I can help you with inventory management, procurement, patient records, billing, and reports. How can I assist you today?',
      timestamp: new Date()
    }]);
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage = {
      role: 'user',
      content: input,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await chatbotAPI.chat({
        message: input,
        session_id: sessionId
      });

      const botMessage = {
        role: 'assistant',
        content: response.data.response,
        intent: response.data.intent,
        confidence: response.data.confidence,
        suggested_actions: response.data.suggested_actions,
        timestamp: new Date(response.data.timestamp)
      };

      setMessages(prev => [...prev, botMessage]);
      
      if (!sessionId) {
        setSessionId(response.data.session_id);
      }
    } catch (error) {
      const errorMessage = {
        role: 'assistant',
        content: 'I apologize, but I encountered an error processing your request. Please try again.',
        timestamp: new Date(),
        error: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSuggestedAction = (action) => {
    setInput(action.label);
  };

  return (
    <div style={{ 
      height: 'calc(100vh - 65px)', 
      display: 'flex',
      flexDirection: 'column',
      background: '#f9fafb'
    }}>
      {/* Header */}
      <div style={{
        background: 'white',
        borderBottom: '1px solid #e5e7eb',
        padding: '20px 24px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '48px',
            height: '48px',
            borderRadius: '12px',
            background: 'linear-gradient(135deg, #667eea, #764ba2)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Bot size={28} color="white" />
          </div>
          <div>
            <h1 style={{ fontSize: '20px', fontWeight: '600', marginBottom: '2px' }}>
              AI Assistant
            </h1>
            <p style={{ fontSize: '14px', color: '#6b7280' }}>
              Ask me anything about your clinic operations
            </p>
          </div>
        </div>
      </div>

      {/* Messages Container */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '24px',
        display: 'flex',
        flexDirection: 'column',
        gap: '16px'
      }}>
        {messages.map((message, index) => (
          <div
            key={index}
            style={{
              display: 'flex',
              gap: '12px',
              alignItems: 'flex-start',
              flexDirection: message.role === 'user' ? 'row-reverse' : 'row'
            }}
          >
            {/* Avatar */}
            <div style={{
              width: '40px',
              height: '40px',
              borderRadius: '50%',
              background: message.role === 'user' 
                ? 'linear-gradient(135deg, #2563eb, #3b82f6)' 
                : 'linear-gradient(135deg, #667eea, #764ba2)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0
            }}>
              {message.role === 'user' ? (
                <User size={20} color="white" />
              ) : (
                <Bot size={20} color="white" />
              )}
            </div>

            {/* Message Content */}
            <div style={{
              maxWidth: '70%',
              display: 'flex',
              flexDirection: 'column',
              gap: '8px'
            }}>
              <div style={{
                padding: '12px 16px',
                borderRadius: '12px',
                background: message.role === 'user' ? '#2563eb' : 'white',
                color: message.role === 'user' ? 'white' : '#111827',
                boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
                border: message.error ? '1px solid #ef4444' : 'none'
              }}>
                <p style={{
                  margin: 0,
                  fontSize: '14px',
                  lineHeight: '1.6',
                  whiteSpace: 'pre-wrap'
                }}>
                  {message.content}
                </p>
              </div>

              {/* Suggested Actions */}
              {message.suggested_actions && message.suggested_actions.length > 0 && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                  {message.suggested_actions.map((action, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSuggestedAction(action)}
                      style={{
                        padding: '6px 12px',
                        fontSize: '12px',
                        background: '#eff6ff',
                        color: '#2563eb',
                        border: '1px solid #bfdbfe',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        fontWeight: '500'
                      }}
                    >
                      {action.label}
                    </button>
                  ))}
                </div>
              )}

              {/* Metadata */}
              <div style={{
                fontSize: '11px',
                color: '#9ca3af',
                display: 'flex',
                gap: '8px',
                alignItems: 'center'
              }}>
                <span>{formatDateTime(message.timestamp)}</span>
                {message.intent && (
                  <>
                    <span>•</span>
                    <span>{message.intent}</span>
                  </>
                )}
                {message.confidence && (
                  <>
                    <span>•</span>
                    <span>{(message.confidence * 100).toFixed(0)}% confidence</span>
                  </>
                )}
              </div>
            </div>
          </div>
        ))}

        {loading && (
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            <div style={{
              width: '40px',
              height: '40px',
              borderRadius: '50%',
              background: 'linear-gradient(135deg, #667eea, #764ba2)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Bot size={20} color="white" />
            </div>
            <div style={{
              padding: '12px 16px',
              borderRadius: '12px',
              background: 'white',
              boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
              display: 'flex',
              gap: '8px',
              alignItems: 'center'
            }}>
              <Loader size={16} className="spinner" />
              <span style={{ fontSize: '14px', color: '#6b7280' }}>Thinking...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div style={{
        background: 'white',
        borderTop: '1px solid #e5e7eb',
        padding: '20px 24px'
      }}>
        <div style={{
          display: 'flex',
          gap: '12px',
          alignItems: 'flex-end'
        }}>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message here... (Press Enter to send)"
            disabled={loading}
            style={{
              flex: 1,
              padding: '12px 16px',
              border: '1px solid #e5e7eb',
              borderRadius: '12px',
              fontSize: '14px',
              resize: 'none',
              minHeight: '48px',
              maxHeight: '120px',
              fontFamily: 'inherit'
            }}
            rows={1}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || loading}
            style={{
              padding: '12px 20px',
              background: input.trim() && !loading ? '#2563eb' : '#e5e7eb',
              color: input.trim() && !loading ? 'white' : '#9ca3af',
              border: 'none',
              borderRadius: '12px',
              cursor: input.trim() && !loading ? 'pointer' : 'not-allowed',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '14px',
              fontWeight: '600',
              transition: 'all 0.2s'
            }}
          >
            <Send size={18} />
            Send
          </button>
        </div>
      </div>
    </div>
  );
};

export default Chatbot;
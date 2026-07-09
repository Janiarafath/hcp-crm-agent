import React, { useState, useRef, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { sendMessage, addChatMessage } from '../store/crmSlice';

const ChatInterface = () => {
  const [inputMessage, setInputMessage] = useState('');
  const dispatch = useDispatch();
  const { chatMessages, loading, error } = useSelector((state) => state.crm);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatMessages]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || loading) return;

    dispatch(addChatMessage({ role: 'user', content: inputMessage }));
    dispatch(sendMessage(inputMessage));
    setInputMessage('');
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="chat-interface">
      <h2>AI Assistant</h2>
      
      <div className="chat-messages">
        {chatMessages.length === 0 && (
          <div className="welcome-message">
            <p>Welcome! Describe your HCP interaction and I'll help you log it.</p>
            <p className="example">
              Example: "Met Dr. Smith today and discussed Product X efficacy. The meeting was positive, I shared the brochure and clinical data."
            </p>
          </div>
        )}
        
        {chatMessages.map((msg, index) => (
          <div key={index} className={`message ${msg.role}`}>
            <div className="message-content">
              {msg.content}
              {msg.toolCalls && msg.toolCalls.length > 0 && (
                <div className="tool-calls">
                  <span className="tool-badge">Tools used: </span>
                  {msg.toolCalls.map((call, i) => (
                    <span key={i} className="tool-name">{call.tool}</span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        
        {loading && (
          <div className="message assistant loading">
            <div className="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      <div className="chat-input">
        <textarea
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Describe your HCP interaction..."
          rows="3"
          disabled={loading}
        />
        <button 
          onClick={handleSendMessage} 
          disabled={!inputMessage.trim() || loading}
          className="send-button"
        >
          {loading ? 'Processing...' : 'Log'}
        </button>
      </div>
    </div>
  );
};

export default ChatInterface;

import React, { useState, useRef, useEffect } from 'react';

const ChatInterface = ({ messages, onSendMessage, isLoading }) => {
    const [input, setInput] = useState('');
    const bottomRef = useRef(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, isLoading]);

    const handleSend = () => {
        if (!input.trim() || isLoading) return;
        onSendMessage(input);
        setInput('');
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    return (
        <div className="chat-container">
            <div className="messages-area">
                {messages.map((msg, idx) => (
                    <div key={idx} className="message">
                        <div className={`avatar ${msg.role === 'user' ? 'user-avatar' : 'ai-avatar'}`}>
                            {msg.role === 'user' ? 'U' : 'AI'}
                        </div>
                        <div className="message-content">
                            <div style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</div>

                            {/* Display Tool Calls if present */}
                            {msg.tool_calls && msg.tool_calls.length > 0 && (
                                <div style={{ marginTop: '8px' }}>
                                    {msg.tool_calls.map((tool, tIdx) => (
                                        <div key={tIdx} className="tool-badge">
                                            ⚙️ Used Tool: {tool.name}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                ))}
                {isLoading && (
                    <div className="message">
                        <div className="avatar ai-avatar">AI</div>
                        <div className="message-content">
                            <span className="loading-dots">Thinking</span>
                        </div>
                    </div>
                )}
                <div ref={bottomRef} />
            </div>

            <div className="input-area">
                <div className="input-wrapper">
                    <textarea
                        className="chat-input"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Ask anything..."
                        rows={1}
                    />
                    <button
                        className="send-btn"
                        onClick={handleSend}
                        disabled={isLoading || !input.trim()}
                    >
                        ➤
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ChatInterface;

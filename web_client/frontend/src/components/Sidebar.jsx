import React from 'react';

const Sidebar = ({ sessions, currentSessionId, onSelectSession, onNewSession }) => {
  return (
    <div className="sidebar">
      <button className="new-chat-btn" onClick={onNewSession}>
        <span>+</span> New Chat
      </button>
      
      <div className="history-list">
        {sessions.map((session) => (
          <div 
            key={session.id}
            className={`history-item ${session.id === currentSessionId ? 'active' : ''}`}
            onClick={() => onSelectSession(session.id)}
          >
            {session.last_message ? 
              (session.last_message.length > 25 ? session.last_message.substring(0, 25) + '...' : session.last_message) 
              : 'New Conversation'}
          </div>
        ))}
      </div>
    </div>
  );
};

export default Sidebar;

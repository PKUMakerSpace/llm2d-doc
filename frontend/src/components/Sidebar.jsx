// frontend/src/components/Sidebar.jsx
// import React from 'react';
import PropTypes from 'prop-types';
import '../App.css';

const Sidebar = ({ isOpen, onClose, messages }) => {
  return (
    <>
      {isOpen && (
        <div className="sidebar-overlay" onClick={onClose}></div>
      )}
      <div className={`sidebar ${isOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <h3>聊天记录</h3>
          <button className="sidebar-close-btn" onClick={onClose}>
            ×
          </button>
        </div>
        <div className="sidebar-content">
          {messages.map((msg, index) => (
            <div key={index} className={`sidebar-message ${msg.type}`}>
              <strong>{msg.type === 'user' ? '你' : '助手'}：</strong>
              <span>{msg.content}</span>
            </div>
          ))}
        </div>
      </div>
    </>
  );
};

Sidebar.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  messages: PropTypes.arrayOf(
    PropTypes.shape({
      type: PropTypes.string.isRequired,
      content: PropTypes.string.isRequired
    })
  ).isRequired
};

export default Sidebar;
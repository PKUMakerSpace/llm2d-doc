  // frontend/src/components/Chat/InputArea.jsx
  import '../../App.css';
  import PropTypes from 'prop-types'; // 引入 PropTypes
  
  const InputArea = ({ 
    input, 
    setInput, 
    onSendMessage,
    fileInputRef,
    onFileUpload,
    disabled 
  }) => {
    const handleSendMessage = () => {
      if (input.trim() && !disabled) {
        onSendMessage(input);
        setInput('');
      }
    };
  
    const handleKeyPress = (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSendMessage();
      }
    };
  
    return (
      <div className="chat-input-container">
        {/* 上传按钮 */}
        <button
          style={{ marginRight: 8 }}
          onClick={() => fileInputRef.current?.click()}
          title="上传文档"
          disabled={disabled}
        >
          +
        </button>
        <input
          type="file"
          ref={fileInputRef}
          style={{ display: 'none' }}
          accept=".pdf,.doc,.docx"
          onChange={e => e.target.files[0] && onFileUpload(e.target.files[0])}
        />
        {/* 聊天输入框 */}
        <input
          className="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyPress}
          placeholder="输入消息..."
          disabled={disabled}
        />
        <button 
          className="chat-submit-button"
          onClick={handleSendMessage}
          disabled={disabled || !input.trim()}
        >
          发送
        </button>
      </div>
    );
  };
  
  // 添加 PropTypes 验证
  InputArea.propTypes = {
    input: PropTypes.string.isRequired,
    setInput: PropTypes.func.isRequired,
    onSendMessage: PropTypes.func.isRequired,
    fileInputRef: PropTypes.object.isRequired,
    onFileUpload: PropTypes.func.isRequired,
    disabled: PropTypes.bool.isRequired,
  };
  
  export default InputArea;
import React, { useState, useEffect } from 'react';
import '../App.css';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const TTSToggle = ({ ttsEnabled: propTtsEnabled, onToggle }) => {
  const [localTtsEnabled, setLocalTtsEnabled] = useState(true);
  const [ttsApiKeyValid, setTtsApiKeyValid] = useState(false);
  const [loading, setLoading] = useState(false);
  const ttsEnabled = propTtsEnabled !== undefined ? propTtsEnabled : localTtsEnabled;

  // 获取TTS状态
  const fetchTtsStatus = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/tts/status`);
      const data = await response.json();
      setLocalTtsEnabled(data.enabled);
      setTtsApiKeyValid(data.api_key_valid);
      if (onToggle) {
        onToggle(data.enabled);
      }
    } catch (error) {
      console.error('获取TTS状态失败:', error);
    }
  };

  // 切换TTS状态
  const toggleTts = async (enabled) => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/tts/toggle`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ enabled }),
      });
      const data = await response.json();
      setLocalTtsEnabled(data.enabled);
      console.log(data.message);
      if (onToggle) {
        onToggle(data.enabled);
      }
    } catch (error) {
      console.error('切换TTS状态失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 组件加载时获取初始状态
  useEffect(() => {
    fetchTtsStatus();
  }, []);

  return (
    <div className="tts-toggle-container">
      <label className="tts-toggle-label">
        <button
          className={`tts-toggle-btn ${ttsEnabled ? 'enabled' : 'disabled'}
            ${!ttsApiKeyValid ? 'api-key-invalid' : ''}`}
          onClick={() => !ttsApiKeyValid || toggleTts(!ttsEnabled)}
          disabled={loading || !ttsApiKeyValid}
          title={!ttsApiKeyValid ? '⚠️ TTS API密钥无效' : `语音播报已${ttsEnabled ? '开启' : '关闭'}`}
          style={{
            padding: '8px 16px',
            fontSize: '14px',
            fontWeight: 'bold',
            minWidth: '90px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
            textShadow: '0 1px 1px rgba(0,0,0,0.3)',
            border: '1px solid rgba(255,255,255,0.2)',
            transition: 'all 0.3s ease',
            backgroundColor: ttsEnabled ? '#4CAF50' : '#666',
            color: 'white',
            borderRadius: '6px',
            cursor: (loading || !ttsApiKeyValid) ? 'not-allowed' : 'pointer'
          }}
        >
          {loading ? '⏳' : (ttsEnabled ? '🔊 开启' : '🔇 关闭')}
        </button>
      </label>
    </div>
  );
};

export default TTSToggle;
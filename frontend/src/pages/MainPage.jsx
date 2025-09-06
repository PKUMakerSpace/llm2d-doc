// frontend/src/pages/MainPage.jsx
import { useState, useRef } from 'react';
import Live2DController from '../components/Live2D/Live2DController';
import MessageList from '../components/Chat/MessageList';
import InputArea from '../components/Chat/InputArea';
import '../App.css';
import LoadingDots from '../components/LoadingDots';

export default function MainPage() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const fileInputRef = useRef();
  const [subtitleSentences, setSubtitleSentences] = useState([]);
  const [subtitleIndex, setSubtitleIndex] = useState(0);
  
  // Live2D 控制器 ref
  const live2dControllerRef = useRef(null);

  // 拆分为句子数组
    const splitSentences = (text) => {
      return text.split(/(?<=[。！？?!])/).filter(s => s.trim().length > 0);
    };

  // 播放每一句语音并切换字幕
  const playSentences = async (sentences, audioBase64, audioSegments = null) => {
    setSubtitleSentences(sentences);
    setSubtitleIndex(0);
    
    // If we have separate audio segments, play them one by one
    if (audioSegments && audioSegments.length === sentences.length) {
      for (let i = 0; i < sentences.length; i++) {
        setSubtitleIndex(i);
        const audioSegment = audioSegments[i];
        
        if (audioSegment && audioSegment.length > 0) {
          try {
            const audioBlob = new Blob(
              [Uint8Array.from(atob(audioSegment), c => c.charCodeAt(0))],
              { type: 'audio/mpeg' }
            );
            const audioUrl = URL.createObjectURL(audioBlob);
            const audio = new Audio(audioUrl);
            
            audio.onerror = (e) => {
              console.error('Audio playback error:', e);
            };
            
            await audio.play();
            
            // Wait for audio to finish or error
            await new Promise(resolve => {
              audio.onended = resolve;
              audio.onerror = () => resolve();
            });
            
            URL.revokeObjectURL(audioUrl);
          } catch (audioError) {
            console.error('Audio processing error:', audioError);
            // Wait for a default time if audio fails
            await new Promise(resolve => setTimeout(resolve, 2000));
          }
        } else {
          // If no audio for this sentence, wait for a default time
          await new Promise(resolve => setTimeout(resolve, 2000));
        }
      }
    } else if (audioBase64 && audioBase64.length > 0) {
      // Fallback to the old method with single audio file
      try {
        const audioBlob = new Blob(
          [Uint8Array.from(atob(audioBase64), c => c.charCodeAt(0))],
          { type: 'audio/mpeg' }
        );
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        
        audio.onerror = (e) => {
          console.error('Audio playback error:', e);
        };
        
        // Play the entire audio
        await audio.play();
        
        // Calculate timing for each sentence based on audio duration
        const totalDuration = audio.duration || sentences.length * 2; // fallback to 2s per sentence
        const timePerSentence = totalDuration / sentences.length;
        
        // Update subtitles at calculated intervals
        const intervals = [];
        for (let i = 0; i < sentences.length; i++) {
          intervals.push(setTimeout(() => {
            setSubtitleIndex(i);
          }, i * timePerSentence * 1000));
        }
        
        // Wait for audio to finish
        await new Promise(resolve => {
          audio.onended = () => {
            intervals.forEach(clearTimeout);
            resolve();
          };
          audio.onerror = () => {
            intervals.forEach(clearTimeout);
            resolve();
          };
        });
        
        URL.revokeObjectURL(audioUrl);
      } catch (audioError) {
        console.error('Audio processing error:', audioError);
        // Fallback to sequential display if audio fails
        for (let i = 0; i < sentences.length; i++) {
          setSubtitleIndex(i);
          await new Promise(resolve => setTimeout(resolve, 2000));
        }
      }
    } else {
      // If no audio at all, just display subtitles sequentially
      for (let i = 0; i < sentences.length; i++) {
        setSubtitleIndex(i);
        await new Promise(resolve => setTimeout(resolve, 2000));
      }
    }
    
    // Clear subtitles after completion with a small delay
    setTimeout(() => {
      setSubtitleSentences([]);
      setSubtitleIndex(0);
      
      // Reset expression after all speech is done
      if (live2dControllerRef.current) {
        live2dControllerRef.current.resetExpression();
      }
    }, 1000);
  };

 /**
   * 处理用户发送消息的函数
   * 
   * @param {string} message - 用户发送的消息内容
   * 
   * @description
   * 该函数负责处理用户发送的消息，包括：
   * 1. 向后端API发送消息请求
   * 2. 接收并处理AI回复
   * 3. 控制Live2D模型的表情变化
   * 4. 更新消息列表状态
   * 5. 处理语音播放和字幕显示
   * 
   * @example
   * handleSendMessage("你好，今天天气怎么样？");
   * 
   * @returns {Promise<void>} 无返回值的异步函数
   */
  const handleSendMessage = async (message) => {
    if (!message.trim()) return;
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          message: message,
          session_id: 'default' 
        }),
      });
      
      const data = await response.json();
      
      // 设置表情
      if (data.expression && live2dControllerRef.current) {
        live2dControllerRef.current.showExpression(data.expression);
      }
      
      // Instead of directly playing audio, use the subtitle system
      // Split response into sentences for subtitle display
      const sentences = splitSentences(data.message);
      
      // Update messages first
      setMessages([
        ...messages,
        { type: 'user', content: message },
        { type: 'assistant', content: data.message }
      ]);
      
      // Play sentences with audio through subtitle system
      if (data.audio_segments && data.sentences) {
        // New format with separate audio segments
        await playSentences(data.sentences, null, data.audio_segments);
      } else if (data.audio && data.audio.length > 0) {
        // Old format with single audio file
        await playSentences(sentences, data.audio);
      } else {
        // No audio, just display subtitles
        setSubtitleSentences(sentences);
        setSubtitleIndex(0);
        // Simulate timing for subtitle display without audio
        for (let i = 0; i < sentences.length; i++) {
          setSubtitleIndex(i);
          await new Promise(resolve => setTimeout(resolve, 2000));
        }
        // Clear subtitles after completion
        setTimeout(() => {
          setSubtitleSentences([]);
          setSubtitleIndex(0);
          
          // Reset expression
          if (live2dControllerRef.current) {
            live2dControllerRef.current.resetExpression();
          }
        }, 1000);
      }
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  // 文件上传处理
  const handleUpload = async (file) => {
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/upload', {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      
      // Update messages first
      setMessages([
        ...messages,
        { type: 'user', content: '上传文档并请求总结' },
        { type: 'assistant', content: data.summary }
      ]);
      
      // Split summary into sentences
      const sentences = splitSentences(data.summary);
      
      // Play sentences with audio through subtitle system
      if (data.audio_segments && data.sentences) {
        // New format with separate audio segments
        await playSentences(data.sentences, null, data.audio_segments);
      } else if (data.audio && data.audio.length > 0) {
        // Old format with single audio file
        await playSentences(sentences, data.audio);
      } else {
        // No audio, just display subtitles
        setSubtitleSentences(sentences);
        setSubtitleIndex(0);
        // Simulate timing for subtitle display without audio
        for (let i = 0; i < sentences.length; i++) {
          setSubtitleIndex(i);
          await new Promise(resolve => setTimeout(resolve, 2000));
        }
        // Clear subtitles after completion
        setTimeout(() => {
          setSubtitleSentences([]);
          setSubtitleIndex(0);
          
          // Reset expression
          if (live2dControllerRef.current) {
            live2dControllerRef.current.resetExpression();
          }
        }, 1000);
      }
    } catch (error) {
      console.error('上传失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 获取最后一条助手消息
  const lastAssistantMessage = messages
    .filter(msg => msg.type === 'assistant')
    .at(-1);

  return (
    <div className="app">
      <div className="live2d-main">
        <Live2DController ref={live2dControllerRef} />
        <div className="subtitles">
          {loading && subtitleSentences.length === 0 ? (
            <div className="subtitle-text loading">
              <LoadingDots />
            </div>
          ) : subtitleSentences.length > 0 ? (
            <div className="subtitle-text">
              {subtitleSentences[subtitleIndex]}
            </div>
          ) : lastAssistantMessage && (
            <div className="subtitle-text">
              {lastAssistantMessage.content}
            </div>
          )}
        </div>
      </div>

      <MessageList messages={messages} />
      <InputArea 
        input={input}
        setInput={setInput}
        onSendMessage={handleSendMessage}
        fileInputRef={fileInputRef}
        onFileUpload={handleUpload}
        disabled={loading}
      />
    </div>
  );
}
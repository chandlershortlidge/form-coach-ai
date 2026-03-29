import { useState, useCallback, useEffect, useRef } from 'react';
import ChatPanel from './components/ChatPanel';
import InputBar from './components/InputBar';
import { analyze } from './utils/api';
import { getSessionId } from './utils/session';

const sessionId = getSessionId();

export default function App() {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingType, setLoadingType] = useState(null);
  const [previewData, setPreviewData] = useState(null);
  const [videoFile, setVideoFile] = useState(null);
  const videoUrlRef = useRef(null);
  const [videoUrl, setVideoUrl] = useState(null);

  // Create/revoke object URL when videoFile changes
  useEffect(() => {
    if (videoFile) {
      const url = URL.createObjectURL(videoFile);
      videoUrlRef.current = url;
      setVideoUrl(url);
    } else {
      setVideoUrl(null);
    }
    return () => {
      if (videoUrlRef.current) {
        URL.revokeObjectURL(videoUrlRef.current);
        videoUrlRef.current = null;
      }
    };
  }, [videoFile]);

  const addMessage = useCallback((msg) => {
    setMessages((prev) => [...prev, msg]);
  }, []);

  const updateMessage = useCallback((index, updates) => {
    setMessages((prev) => prev.map((m, i) => (i === index ? { ...m, ...updates } : m)));
  }, []);

  async function sendToBackend(payload, userMsgIndex, type = 'text') {
    setIsLoading(true);
    setLoadingType(type);
    try {
      await analyze({
        sessionId,
        ...payload,
        onResponse(response, transcription) {
          if (transcription && userMsgIndex != null) {
            updateMessage(userMsgIndex, { text: `🎙️ ${transcription}` });
          }
          addMessage({ role: 'coach', text: response });
        },
      });
    } catch (err) {
      console.error('[sendToBackend] error:', err);
      addMessage({ role: 'error', text: 'Something went wrong. Please try again.' });
    } finally {
      setIsLoading(false);
      setLoadingType(null);
    }
  }

  function handleSendText(text) {
    addMessage({ role: 'user', text });
    sendToBackend({ userQuery: text });
  }

  async function handleSendVideo(file, textInput) {
    const display = textInput
      ? `📎 ${file.name}\n${textInput}`
      : `📎 ${file.name}`;
    addMessage({ role: 'user', text: display });
    setVideoFile(file);
    setIsLoading(true);
    setLoadingType('video');
    setPreviewData(null);

    try {
      await analyze({
        sessionId,
        userVideo: file,
        userQuery: textInput || 'Analyze my form',
        onStatus(message) {
          console.log('[sse] status:', message);
        },
        onPreview(classifiedKeywords) {
          console.log('[sse] preview:', classifiedKeywords);
          setPreviewData(classifiedKeywords);
        },
        onResponse(response) {
          addMessage({ role: 'coach', text: response });
        },
      });
    } catch (err) {
      console.error('[sendToBackend] error:', err);
      addMessage({ role: 'error', text: 'Something went wrong. Please try again.' });
    } finally {
      setIsLoading(false);
      setLoadingType(null);
      setPreviewData(null);
    }
  }

  function handleSendAudio(blob) {
    const idx = messages.length;
    addMessage({ role: 'user', text: '🎙️ Voice message' });
    sendToBackend({ userAudio: blob }, idx);
  }

  return (
    <div className={`app${videoUrl ? ' has-video' : ''}`}>
      <h1 className="app-title">Fitness Form Coach</h1>
      <div className="app-layout">
        <div className="chat-panel">
          <ChatPanel messages={messages} isLoading={isLoading} loadingType={loadingType} previewData={previewData} />
          <InputBar
            onSendText={handleSendText}
            onSendVideo={handleSendVideo}
            onSendAudio={handleSendAudio}
            disabled={isLoading}
          />
        </div>
        {videoUrl && (
          <div className="video-panel">
            <div className="video-panel-header">
              <span className="video-panel-title">Your Video</span>
              <button
                className="video-panel-close"
                onClick={() => setVideoFile(null)}
                aria-label="Close video panel"
              >
                ✕
              </button>
            </div>
            <video
              className="video-player"
              src={videoUrl}
              controls
              playsInline
              preload="metadata"
            />
          </div>
        )}
      </div>
    </div>
  );
}

import { useState, useCallback, useEffect, useRef } from 'react';
import ChatPanel from './components/ChatPanel';
import InputBar from './components/InputBar';
import Sidebar from './components/Sidebar';
import { analyze, fetchSessions, fetchSession } from './utils/api';
import { getSessionId, resetSessionId } from './utils/session';

export default function App() {
  const [sessionId, setSessionId] = useState(getSessionId);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingType, setLoadingType] = useState(null);
  const [previewData, setPreviewData] = useState(null);
  const [videoFile, setVideoFile] = useState(null);
  const videoUrlRef = useRef(null);
  const [videoUrl, setVideoUrl] = useState(null);
  const [sessionHistory, setSessionHistory] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');

  // Load session list from backend on mount and after each analysis
  function refreshSessions() {
    fetchSessions().then(setSessionHistory).catch(() => {});
  }

  useEffect(() => {
    refreshSessions();
  }, []);

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

  function handleNewSession() {
    const newId = resetSessionId();
    setSessionId(newId);
    setMessages([]);
    setVideoFile(null);
    setPreviewData(null);
    setIsLoading(false);
    setLoadingType(null);
  }

  async function handleSelectSession(id) {
    try {
      const session = await fetchSession(id);
      if (session.error) return;

      // Switch to this session
      sessionStorage.setItem('session_id', id);
      setSessionId(id);
      setVideoFile(null);
      setPreviewData(null);
      setIsLoading(false);
      setLoadingType(null);

      // Rebuild messages from saved session data
      const restored = [];
      if (session.user_query) {
        const prefix = session.video_filename ? `📎 ${session.video_filename}\n` : '';
        restored.push({ role: 'user', text: `${prefix}${session.user_query}` });
      }
      if (session.response) {
        restored.push({ role: 'coach', text: session.response });
      }
      setMessages(restored);
    } catch (err) {
      console.error('[sidebar] failed to load session:', err);
    }
  }

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
          refreshSessions();
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
          refreshSessions();
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

  // Build session list for sidebar
  const sidebarSessions = sessionHistory.map((s) => {
    let date = '';
    if (s.created_at) {
      const d = new Date(s.created_at);
      const day = d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      const time = d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
      date = `${day}, ${time}`;
    }
    return {
      id: s.session_id,
      label: s.exercise_label || s.video_filename || 'Untitled session',
      date,
      active: s.session_id === sessionId,
    };
  });

  return (
    <div className={`app${videoUrl ? ' has-video' : ''}`}>
      <Sidebar
        sessions={sidebarSessions}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        onNewSession={handleNewSession}
        onSelectSession={handleSelectSession}
      />
      <div className="app-main">
        <div className="app-header">
          <h1 className="app-title">FormCoach <span className="app-title-ai">AI</span></h1>
          <p className="app-tagline">AI-powered analysis for your lifts</p>
        </div>
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
                autoPlay
                loop
                muted
                playsInline
                preload="metadata"
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

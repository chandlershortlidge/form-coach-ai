import { useState, useCallback } from 'react';
import ChatPanel from './components/ChatPanel';
import InputBar from './components/InputBar';
import { analyze, preview } from './utils/api';
import { getSessionId } from './utils/session';

const sessionId = getSessionId();

export default function App() {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingType, setLoadingType] = useState(null);
  const [previewData, setPreviewData] = useState(null);

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
      const data = await analyze({ sessionId, ...payload });
      if (data.transcription && userMsgIndex != null) {
        updateMessage(userMsgIndex, { text: `🎙️ ${data.transcription}` });
      }
      addMessage({ role: 'coach', text: data.response });
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
    setIsLoading(true);
    setLoadingType('video');
    setPreviewData(null);

    // Fire preview as fire-and-forget — don't block on it
    let previewStale = false;
    preview({ sessionId, userVideo: file })
      .then((data) => {
        if (!previewStale) {
          console.log('[preview] result:', data);
          setPreviewData(data);
        }
      })
      .catch((err) => console.error('[preview] error:', err));

    try {
      const data = await analyze({
        sessionId,
        userVideo: file,
        userQuery: textInput || 'Analyze my form',
      });
      previewStale = true;
      addMessage({ role: 'coach', text: data.response });
    } catch (err) {
      previewStale = true;
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
    <div className="app">
      <h1 className="app-title">Fitness Form Coach</h1>
      <div className="chat-panel">
        <ChatPanel messages={messages} isLoading={isLoading} loadingType={loadingType} previewData={previewData} />
        <InputBar
          onSendText={handleSendText}
          onSendVideo={handleSendVideo}
          onSendAudio={handleSendAudio}
          disabled={isLoading}
        />
      </div>
    </div>
  );
}

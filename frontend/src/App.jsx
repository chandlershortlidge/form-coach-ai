import { useState, useCallback } from 'react';
import ChatPanel from './components/ChatPanel';
import InputBar from './components/InputBar';
import { analyze } from './utils/api';
import { getSessionId } from './utils/session';

const sessionId = getSessionId();

export default function App() {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingType, setLoadingType] = useState(null);

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

  function handleSendVideo(file, textInput) {
    const display = textInput
      ? `📎 ${file.name}\n${textInput}`
      : `📎 ${file.name}`;
    addMessage({ role: 'user', text: display });
    sendToBackend({
      userVideo: file,
      userQuery: textInput || 'Analyze my form',
    }, undefined, 'video');
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
        <ChatPanel messages={messages} isLoading={isLoading} loadingType={loadingType} />
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

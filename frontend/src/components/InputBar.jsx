import { useRef, useState } from 'react';

export default function InputBar({ onSendText, onSendVideo, onSendAudio, disabled }) {
  const [text, setText] = useState('');
  const [recording, setRecording] = useState(false);
  const [stagedVideo, setStagedVideo] = useState(null);
  const fileRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);

  function handleSubmit(e) {
    e.preventDefault();
    const trimmed = text.trim();
    if (disabled) return;

    if (stagedVideo) {
      onSendVideo(stagedVideo, trimmed);
      setStagedVideo(null);
      setText('');
      fileRef.current.value = '';
      return;
    }

    if (!trimmed) return;
    onSendText(trimmed);
    setText('');
  }

  function handleFileChange(e) {
    const file = e.target.files?.[0];
    if (!file || disabled) return;
    setStagedVideo(file);
    fileRef.current.value = '';
  }

  function clearStagedVideo() {
    setStagedVideo(null);
  }

  async function toggleRecording() {
    if (disabled) return;

    if (recording) {
      mediaRecorderRef.current?.stop();
      setRecording(false);
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        stream.getTracks().forEach((t) => t.stop());
        onSendAudio(blob);
      };

      mediaRecorderRef.current = recorder;
      recorder.start();
      setRecording(true);
    } catch {
      // Permission denied or not available
    }
  }

  return (
    <div className="input-bar-wrapper">
      <div className="empty-state-hints">
        <p className="empty-state-hint">Drop a video, type a question, or use voice — the coach handles all three.</p>
        <p className="empty-state-hint">Shorter clips = faster feedback.</p>
      </div>
      {stagedVideo && (
        <div className="video-chip">
          <span className="video-chip-name">📎 {stagedVideo.name}</span>
          <button
            type="button"
            className="video-chip-remove"
            onClick={clearStagedVideo}
            aria-label="Remove video"
          >
            ✕
          </button>
        </div>
      )}
      <form className="input-bar" onSubmit={handleSubmit}>
        <button
          type="button"
          className="icon-btn"
          onClick={() => fileRef.current?.click()}
          aria-label="Upload video"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48" />
          </svg>
        </button>

        <input
          ref={fileRef}
          type="file"
          accept="video/mp4,video/quicktime,video/avi,video/webm"
          onChange={handleFileChange}
          hidden
        />

        <input
          type="text"
          className="text-input"
          placeholder="Tip: Keep videos between 10-15 seconds"
          value={text}
          onChange={(e) => setText(e.target.value)}
          disabled={disabled}
        />

        <button
          type="button"
          className={`icon-btn mic-btn${recording ? ' recording' : ''}`}
          onClick={toggleRecording}
          aria-label={recording ? 'Stop recording' : 'Start recording'}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3z" />
            <path d="M19 10v2a7 7 0 01-14 0v-2" />
            <line x1="12" y1="19" x2="12" y2="23" />
            <line x1="8" y1="23" x2="16" y2="23" />
          </svg>
        </button>
      </form>
    </div>
  );
}

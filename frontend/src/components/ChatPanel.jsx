import { useEffect, useRef, useState } from 'react';

function parseCoachResponse(text) {
  if (!text) return [];
  const lines = text.split('\n');
  const elements = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();

    if (trimmed === '') {
      elements.push({ type: 'spacer', key: i });
    } else if (trimmed.startsWith('- ')) {
      elements.push({ type: 'bullet', text: trimmed.slice(2), key: i });
    } else if (/^\d+\)\s/.test(trimmed)) {
      elements.push({ type: 'numbered', text: trimmed, key: i });
    } else if (trimmed.length < 60 && !trimmed.startsWith('-') && !trimmed.includes('. ')) {
      elements.push({ type: 'header', text: trimmed, key: i });
    } else {
      elements.push({ type: 'paragraph', text: trimmed, key: i });
    }
  }

  return elements;
}

function CoachMessage({ text }) {
  const parts = parseCoachResponse(text);

  return (
    <div className="coach-message">
      {parts.map((part) => {
        switch (part.type) {
          case 'spacer':
            return <div key={part.key} className="spacer" />;
          case 'header':
            return <div key={part.key} className="coach-header">{part.text}</div>;
          case 'bullet':
            return <div key={part.key} className="coach-bullet">- {part.text}</div>;
          case 'numbered':
            return <div key={part.key} className="coach-numbered">{part.text}</div>;
          case 'paragraph':
            return <div key={part.key} className="coach-paragraph">{part.text}</div>;
          default:
            return null;
        }
      })}
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="typing-indicator">
      <span className="dot" />
      <span className="dot" />
      <span className="dot" />
    </div>
  );
}

const VIDEO_STEPS = [
  { delay: 0, text: 'Watching your video...' },
  { delay: 5000, text: 'Okay, let me see that again...' },
  { delay: 12000, text: 'Checking your setup and positioning...' },
  { delay: 22000, text: 'Looking at your bar path and tempo...' },
  { delay: 35000, text: 'Spotted a few things to work on...' },
  { delay: 50000, text: 'Putting your coaching notes together...' },
];

function VideoLoadingIndicator() {
  const [visibleCount, setVisibleCount] = useState(1);

  useEffect(() => {
    const timers = VIDEO_STEPS.slice(1).map((step, i) =>
      setTimeout(() => setVisibleCount(i + 2), step.delay)
    );
    return () => timers.forEach(clearTimeout);
  }, []);

  return (
    <div className="video-loading">
      {VIDEO_STEPS.slice(0, visibleCount).map((step, i) => {
        const isActive = i === visibleCount - 1;
        return (
          <div key={i} className={`video-loading-step${isActive ? '' : ' completed'} fade-in`}>
            {isActive ? <span className="step-spinner" /> : <span className="step-check">✓</span>}
            <span className="step-text">{step.text}</span>
          </div>
        );
      })}
    </div>
  );
}

export default function ChatPanel({ messages, isLoading, loadingType }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  return (
    <div className="chat-messages">
      {messages.map((msg, i) => {
        if (msg.role === 'user') {
          return (
            <div key={i} className="message-row user-row">
              <div className="user-bubble">{msg.text}</div>
            </div>
          );
        }
        if (msg.role === 'error') {
          return (
            <div key={i} className="message-row coach-row">
              <div className="error-message">{msg.text}</div>
            </div>
          );
        }
        return (
          <div key={i} className="message-row coach-row">
            <CoachMessage text={msg.text} />
          </div>
        );
      })}
      {isLoading && (
        <div className="message-row coach-row">
          {loadingType === 'video' ? <VideoLoadingIndicator /> : <TypingIndicator />}
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  );
}

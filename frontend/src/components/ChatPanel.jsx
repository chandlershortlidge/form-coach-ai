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

const CHECKLIST_PREFIXES = [
  'Checking your',
  'Looking at your',
  'Analyzing your',
  'Now examining your',
  'Reviewing your',
];

function parseClassificationRaw(raw) {
  const lines = raw.split('\n').map(l => l.trim()).filter(Boolean);
  const exercise = lines[0] || 'Unknown exercise';
  const checklist = [];
  for (const line of lines.slice(1)) {
    const item = line.replace(/^\d+[.)]\s*/, '');
    if (item) checklist.push(item);
  }
  return { exercise, checklist };
}

function buildVideoSteps(previewData) {
  const steps = ['Watching your video...'];
  if (!previewData) return steps;

  const { exercise, checklist } = parseClassificationRaw(previewData);
  const cleanExercise = exercise.replace(/\*+/g, '').toLowerCase();
  steps.push(`Nice, a ${cleanExercise}! Let me take a closer look...`);

  checklist.forEach((item, i) => {
    const lowerItem = item.toLowerCase();
    const prefix = CHECKLIST_PREFIXES[i % CHECKLIST_PREFIXES.length];
    steps.push(`${prefix} ${lowerItem}...`);
  });

  steps.push('Putting your coaching notes together...');
  return steps;
}

function VideoLoadingIndicator({ previewData }) {
  const [visibleCount, setVisibleCount] = useState(1);
  const stepsRef = useRef(['Watching your video...']);

  useEffect(() => {
    if (previewData) {
      stepsRef.current = buildVideoSteps(previewData);
      setVisibleCount(2);
    }
  }, [previewData]);

  useEffect(() => {
    if (visibleCount < 2) return;
    if (visibleCount >= stepsRef.current.length) return;

    const timer = setTimeout(() => {
      setVisibleCount((c) => c + 1);
    }, 4000);
    return () => clearTimeout(timer);
  }, [visibleCount]);

  const steps = stepsRef.current;

  return (
    <div className="video-loading">
      {steps.slice(0, visibleCount).map((text, i) => {
        const isActive = i === visibleCount - 1;
        return (
          <div key={i} className={`video-loading-step${isActive ? '' : ' completed'} fade-in`}>
            {isActive ? <span className="step-spinner" /> : <span className="step-check">✓</span>}
            <span className="step-text">{text}</span>
          </div>
        );
      })}
    </div>
  );
}

export default function ChatPanel({ messages, isLoading, loadingType, previewData }) {
  const lastMsgRef = useRef(null);
  const prevCountRef = useRef(0);

  useEffect(() => {
    const prevCount = prevCountRef.current;
    prevCountRef.current = messages.length;

    if (messages.length > prevCount && messages.length > 0) {
      // A new message was added — scroll its top into view
      lastMsgRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, [messages]);

  return (
    <div className="chat-messages">
      {messages.map((msg, i) => {
        const isLast = i === messages.length - 1;
        if (msg.role === 'user') {
          return (
            <div key={i} className="message-row user-row" ref={isLast ? lastMsgRef : null}>
              <div className="user-bubble">{msg.text}</div>
            </div>
          );
        }
        if (msg.role === 'error') {
          return (
            <div key={i} className="message-row coach-row" ref={isLast ? lastMsgRef : null}>
              <div className="error-message">{msg.text}</div>
            </div>
          );
        }
        return (
          <div key={i} className="message-row coach-row" ref={isLast ? lastMsgRef : null}>
            <CoachMessage text={msg.text} />
          </div>
        );
      })}
      {isLoading && (
        <div className="message-row coach-row">
          {loadingType === 'video' ? <VideoLoadingIndicator previewData={previewData} /> : <TypingIndicator />}
        </div>
      )}
    </div>
  );
}

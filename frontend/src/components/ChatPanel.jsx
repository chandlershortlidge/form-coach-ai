import ReactMarkdown from 'react-markdown'; 
import { useEffect, useRef, useState } from 'react';

function CoachMessage({ text }) {
  return (
    <div className="coach-message">
      <ReactMarkdown>{text}</ReactMarkdown>
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

  if (messages.length === 0 && !isLoading) {
    return (
      <div className="chat-messages empty-state">
        <div className="empty-state-content">
          <div className="empty-state-icon">🏋️</div>
          <h2 className="empty-state-title">Ready to check your form?</h2>
          <p className="empty-state-subtitle">
            Upload a workout video or ask a question to get started.
          </p>
          <div className="empty-state-chips">
            <span className="suggestion-chip">Bench press tips</span>
            <span className="suggestion-chip">Check my deadlift</span>
            <span className="suggestion-chip">How's my bar path?</span>
          </div>
        </div>
      </div>
    );
  }

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

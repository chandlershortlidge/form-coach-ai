import { useState } from 'react';

export default function Sidebar({ sessions, searchQuery, onSearchChange, onNewSession, onSelectSession }) {
  const [open, setOpen] = useState(false);

  const filtered = searchQuery
    ? sessions.filter((s) =>
        s.label.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : sessions;

  const sidebar = (
    <aside className="sidebar" role="complementary" aria-label="Session navigation">
      <button className="sidebar-new-btn" onClick={() => { onNewSession(); setOpen(false); }}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <line x1="12" y1="5" x2="12" y2="19" />
          <line x1="5" y1="12" x2="19" y2="12" />
        </svg>
        New session
      </button>

      <div className="sidebar-search">
        <svg className="sidebar-search-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="11" cy="11" r="8" />
          <line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
        <input
          type="text"
          className="sidebar-search-input"
          placeholder="Search sessions..."
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
        />
      </div>

      <div className="sidebar-section">
        <div className="sidebar-section-title">Recent Sessions</div>
        {filtered.length === 0 && (
          <div className="sidebar-empty">
            {searchQuery ? 'No matches' : 'No sessions yet'}
          </div>
        )}
        <div className="sidebar-list">
          {filtered.map((s) => (
            <button
              key={s.id}
              className={`sidebar-item${s.active ? ' active' : ''}`}
              onClick={() => { onSelectSession(s.id); setOpen(false); }}
              title={s.label}
            >
              <span className="sidebar-item-icon">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polygon points="23 7 16 12 23 17 23 7" />
                  <rect x="1" y="5" width="15" height="14" rx="2" ry="2" />
                </svg>
              </span>
              <span className="sidebar-item-text">
                <span className="sidebar-item-label">{s.label}</span>
                <span className="sidebar-item-date">{s.date}</span>
              </span>
            </button>
          ))}
        </div>
      </div>

      <div className="sidebar-section sidebar-section-bottom">
        <div className="sidebar-section-title">Video Library</div>
        <div className="sidebar-empty">Coming soon</div>
      </div>
    </aside>
  );

  return (
    <>
      {/* Mobile toggle */}
      <button
        className="sidebar-toggle"
        onClick={() => setOpen((v) => !v)}
        aria-label={open ? 'Close menu' : 'Open menu'}
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          {open ? (
            <>
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </>
          ) : (
            <>
              <line x1="3" y1="6" x2="21" y2="6" />
              <line x1="3" y1="12" x2="21" y2="12" />
              <line x1="3" y1="18" x2="21" y2="18" />
            </>
          )}
        </svg>
      </button>

      {/* Desktop: always visible */}
      <div className="sidebar-desktop">{sidebar}</div>

      {/* Mobile: drawer overlay */}
      {open && (
        <>
          <div className="sidebar-overlay" onClick={() => setOpen(false)} />
          <div className="sidebar-mobile">{sidebar}</div>
        </>
      )}
    </>
  );
}

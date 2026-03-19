CSS = """
<style>
/* ===== Font ===== */
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

*, html, body, .stApp, .stMarkdown, p, span, label, div,
h1, h2, h3, h4, h5, h6, textarea, button, input {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont,
                 'Segoe UI', sans-serif !important;
}

/* ===== Global ===== */
.stApp {
    background-color: #F0F1F5 !important;
}

/* ===== Hide Streamlit chrome ===== */
header[data-testid="stHeader"],
#MainMenu,
footer,
.stDeployButton,
div[data-testid="stToolbar"],
div[data-testid="stDecoration"],
div[data-testid="stStatusWidget"],
div[data-testid="stSidebarCollapsedControl"] {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    overflow: hidden !important;
}

.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 1rem !important;
    max-width: 760px !important;
}

/* ===== App title ===== */
.app-title {
    text-align: center;
    padding: 0.5rem 0 0.75rem 0;
}
.app-title h1 {
    color: #1A1A1A !important;
    font-size: 1.5rem !important;
    font-weight: 600 !important;
    margin: 0 !important;
    letter-spacing: -0.3px;
}

/* ===== Chat panel ===== */
.chat-panel {
    background: #FFFFFF;
    border: 1px solid #D1D5DB;
    border-radius: 12px;
    display: flex;
    flex-direction: column;
    min-height: 70vh;
    max-height: 80vh;
    overflow: hidden;
}

.chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 1.5rem 1.5rem 1rem 1.5rem;
}

/* ===== User bubble ===== */
.user-bubble-row {
    display: flex;
    justify-content: flex-end;
    margin-bottom: 1rem;
}
.user-bubble {
    background-color: #1A1A1A;
    color: #FFFFFF;
    padding: 10px 18px;
    border-radius: 20px;
    font-size: 15px;
    max-width: 75%;
    line-height: 1.5;
    word-wrap: break-word;
}

/* ===== Coach response ===== */
.coach-response {
    color: #1A1A1A;
    font-size: 15px;
    line-height: 1.7;
    margin-bottom: 1rem;
    padding: 0 0.25rem;
}
.coach-response strong {
    font-weight: 600;
    display: block;
    margin-top: 1rem;
    margin-bottom: 0.25rem;
}
.coach-response p {
    margin: 0 0 0.5rem 0;
}
.coach-response ul {
    margin: 0 0 0.5rem 0;
    padding-left: 0;
    list-style: none;
}
.coach-response ul li {
    position: relative;
    padding-left: 1rem;
    margin-bottom: 0.4rem;
}
.coach-response ul li::before {
    content: "-";
    position: absolute;
    left: 0;
    color: #1A1A1A;
}
.coach-response ol {
    margin: 0 0 0.5rem 0;
    padding-left: 1.25rem;
}
.coach-response ol li {
    margin-bottom: 0.35rem;
}

/* attachment tag */
.attachment-tag {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: #F0F1F5;
    color: #6B7280;
    font-size: 13px;
    padding: 4px 10px;
    border-radius: 8px;
    margin-bottom: 0.5rem;
}

/* ===== Input bar ===== */
.input-bar {
    border-top: 1px solid #E5E7EB;
    padding: 0.75rem 1rem;
    background: #FFFFFF;
    border-radius: 0 0 12px 12px;
}

.input-bar-inner {
    display: flex;
    align-items: center;
    gap: 8px;
    background: #FFFFFF;
    border: 1px solid #D1D5DB;
    border-radius: 24px;
    padding: 6px 12px;
}

.input-bar-inner:focus-within {
    border-color: #9CA3AF;
    box-shadow: 0 0 0 2px rgba(0,0,0,0.04);
}

/* icon buttons in input bar */
.icon-btn {
    background: none;
    border: none;
    cursor: pointer;
    padding: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #6B7280;
    border-radius: 50%;
    transition: background 0.15s;
    flex-shrink: 0;
}
.icon-btn:hover {
    background: #F0F1F5;
}
.icon-btn svg {
    width: 20px;
    height: 20px;
}

/* ===== Override Streamlit chat_input ===== */
div[data-testid="stChatInput"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}
div[data-testid="stChatInput"] textarea {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    font-size: 14px !important;
    color: #1A1A1A !important;
    padding: 4px 0 !important;
    min-height: 0 !important;
}
div[data-testid="stChatInput"] textarea::placeholder {
    color: #9CA3AF !important;
    font-size: 14px !important;
}
div[data-testid="stChatInput"] button {
    display: none !important;
}

/* ===== Override file uploader (hidden, triggered by icon) ===== */
.hidden-uploader {
    position: absolute;
    width: 0;
    height: 0;
    overflow: hidden;
    opacity: 0;
}

/* mini file uploaders styled to be invisible until needed */
div[data-testid="stFileUploader"] {
    margin: 0 !important;
    padding: 0 !important;
}
div[data-testid="stFileUploader"] > label {
    display: none !important;
}
div[data-testid="stFileUploader"] section {
    background: #F8F9FA !important;
    border: 1.5px dashed #D1D5DB !important;
    border-radius: 12px !important;
    padding: 0.75rem !important;
}
div[data-testid="stFileUploader"] section:hover {
    border-color: #9CA3AF !important;
}
div[data-testid="stFileUploader"] button {
    background: transparent !important;
    color: #1A1A1A !important;
    border: 1px solid #D1D5DB !important;
    border-radius: 8px !important;
    font-size: 13px !important;
}
div[data-testid="stFileUploader"] small {
    color: #9CA3AF !important;
    font-size: 12px !important;
}
div[data-testid="stFileUploader"] div[data-testid="stFileUploaderFile"] {
    background: #F0F1F5 !important;
    border: 1px solid #D1D5DB !important;
    border-radius: 8px !important;
}

/* ===== Spinner ===== */
div[data-testid="stSpinner"] > div {
    color: #6B7280 !important;
}

/* ===== Upload tray (compact row below input) ===== */
.upload-tray {
    display: flex;
    gap: 0.75rem;
    padding: 0.5rem 1rem 0 1rem;
}
.upload-tray > div {
    flex: 1;
}

/* ===== Scrollbar ===== */
.chat-messages::-webkit-scrollbar {
    width: 5px;
}
.chat-messages::-webkit-scrollbar-track {
    background: transparent;
}
.chat-messages::-webkit-scrollbar-thumb {
    background: #D1D5DB;
    border-radius: 3px;
}
.chat-messages::-webkit-scrollbar-thumb:hover {
    background: #9CA3AF;
}
</style>
"""

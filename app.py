import streamlit as st
import uuid
from styles import CSS
from audio_recorder_streamlit import audio_recorder

# --------------- config ---------------
API_URL = "http://127.0.0.1:8000/analyze"

DUMMY_RESPONSE = """Great job getting solid, full-range reps on the flat bench. Here's what I'm seeing and how to tighten it up for power and hypertrophy.

**What looks good**
- Bar comes down to the chest each rep and you keep your glutes on the bench.
- Tempo looks controlled on the way down (not a bounce).

**Key fixes**
- Grip safety and wrist stack: You're using a thumbless/suicide grip and your wrists are bent back. Wrap your thumbs around the bar and seat it lower in the palm (over the heel of the hand). Cue: knuckles to the ceiling, bar stacked over the forearm.
- Touch point and elbow angle: A few reps touch a bit high toward the upper chest with elbows flaring. Aim to touch around the lower chest/nipple line with elbows roughly 45–60° from your torso.
- Scapular setup: Your shoulders look a little loose on the bench. Before unracking, pull your shoulder blades down and back (pinch them into the pad) and keep that upper-back arch the whole set.
- Grip width/forearm vertical: At the bottom your forearms angle inward, suggesting a slightly narrow grip. Widen just enough that forearms are vertical at the chest touch point.
- Leg drive: Feet are quite forward and you're not getting much drive. Plant feet flat and slightly behind the knees, push the floor away and "toward your head" to keep your torso tight without lifting your glutes.
- Head position: Your head pops up on some reps. Keep it glued to the bench, eyes fixed on a spot on the ceiling.

**Quick setup checklist (before every set)**
1. Eyes just under the bar, shoulder blades down/back, slight arch.
2. Feet planted and set for leg drive.
3. Wrap thumbs; bar low in palm; wrists stacked.
4. Unrack to over the shoulder joint, inhale and brace.
5. Lower to lower chest, slight pause, press up and back to the shoulders.

Optional safety: use collars and a spotter or adjustable safeties."""

st.set_page_config(
    page_title="Fitness Form Coach",
    page_icon="🏋️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# --------------- inject CSS ---------------
st.markdown(CSS, unsafe_allow_html=True)

# --------------- session state ---------------
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_video" not in st.session_state:
    st.session_state.pending_video = None
if "pending_audio_bytes" not in st.session_state:
    st.session_state.pending_audio_bytes = None

# --------------- helpers ---------------
SVG_UPLOAD = """<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>"""
SVG_MIC = """<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>"""


def format_coach_response(text: str) -> str:
    """Convert the plain-text coach response into styled HTML."""
    import re
    lines = text.strip().split("\n")
    html_parts = []
    in_list = False
    in_ol = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            if in_ol:
                html_parts.append("</ol>")
                in_ol = False
            continue

        # bold headers like **What looks good**
        header_match = re.match(r"^\*\*(.+?)\*\*$", stripped)
        if header_match:
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            if in_ol:
                html_parts.append("</ol>")
                in_ol = False
            html_parts.append(f"<strong>{header_match.group(1)}</strong>")
            continue

        # ordered list items: "1. ...", "2) ..."
        ol_match = re.match(r"^(\d+)[.)]\s+(.+)", stripped)
        if ol_match:
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            if not in_ol:
                html_parts.append("<ol>")
                in_ol = True
            # process inline bold
            content = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", ol_match.group(2))
            html_parts.append(f"<li>{content}</li>")
            continue

        # unordered list items: "- ..."
        if stripped.startswith("- "):
            if in_ol:
                html_parts.append("</ol>")
                in_ol = False
            if not in_list:
                html_parts.append("<ul>")
                in_list = True
            content = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", stripped[2:])
            html_parts.append(f"<li>{content}</li>")
            continue

        # regular paragraph
        if in_list:
            html_parts.append("</ul>")
            in_list = False
        if in_ol:
            html_parts.append("</ol>")
            in_ol = False
        content = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", stripped)
        html_parts.append(f"<p>{content}</p>")

    if in_list:
        html_parts.append("</ul>")
    if in_ol:
        html_parts.append("</ol>")

    return "\n".join(html_parts)


def render_messages() -> str:
    """Build the HTML for all chat messages."""
    parts = []
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            attachment_html = ""
            if msg.get("attachment"):
                attachment_html = (
                    f'<div class="attachment-tag">📎 {msg["attachment"]}</div>'
                )
            parts.append(
                f'<div class="user-bubble-row">'
                f'<div class="user-bubble">{attachment_html}{msg["content"]}</div>'
                f"</div>"
            )
        else:
            parts.append(
                f'<div class="coach-response">{format_coach_response(msg["content"])}</div>'
            )
    return "\n".join(parts)


# --------------- title ---------------
st.markdown(
    '<div class="app-title"><h1>Fitness Form Coach</h1></div>',
    unsafe_allow_html=True,
)

# --------------- chat panel ---------------
messages_html = render_messages()

# We build the chat panel as a single HTML block for the messages area,
# then use Streamlit widgets for the interactive input below it.
st.markdown(
    f'<div class="chat-panel">'
    f'<div class="chat-messages" id="chat-scroll">{messages_html}</div>'
    f"</div>",
    unsafe_allow_html=True,
)

# auto-scroll to bottom
if st.session_state.messages:
    st.markdown(
        """<script>
        const el = document.getElementById('chat-scroll');
        if (el) el.scrollTop = el.scrollHeight;
        </script>""",
        unsafe_allow_html=True,
    )

# --------------- input section (below panel) ---------------
# Upload row — compact, sits between chat panel and text input
upload_col1, upload_col2 = st.columns(2)
with upload_col1:
    uploaded_video = st.file_uploader(
        "Upload video",
        type=["mp4", "mov", "avi", "webm"],
        key="video_uploader",
        label_visibility="collapsed",
    )
with upload_col2:
    audio_bytes = audio_recorder(
        text="",
        recording_color="#FF6A00",
        neutral_color="#6B7280",
        icon_size="1.5x",
        pause_threshold=2.0,
    )

# Text input via chat_input
user_text = st.chat_input("Ask about your form...")

# --------------- handle submission ---------------
has_new_input = False
query = None
attachment_name = None

# text input
if user_text:
    query = user_text
    has_new_input = True

# video upload (new file detected)
if uploaded_video and uploaded_video != st.session_state.pending_video:
    st.session_state.pending_video = uploaded_video
    attachment_name = uploaded_video.name
    has_new_input = True

# audio recording (new recording detected)
if audio_bytes and audio_bytes != st.session_state.pending_audio_bytes:
    st.session_state.pending_audio_bytes = audio_bytes
    has_new_input = True

if has_new_input:
    display_text = query if query else ""
    # determine what to show for the user message
    if not display_text and attachment_name:
        display_text = "How's my form?"
    elif not display_text and audio_bytes and audio_bytes == st.session_state.pending_audio_bytes:
        display_text = "Voice message recorded"
        attachment_name = "voice recording"

    st.session_state.messages.append({
        "role": "user",
        "content": display_text,
        "attachment": attachment_name,
    })

    # --- dummy response (swap for real API call later) ---
    st.session_state.messages.append({
        "role": "coach",
        "content": DUMMY_RESPONSE,
    })

    st.rerun()

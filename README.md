# FormCoach AI

A multimodal AI coaching system that analyzes workout videos and user queries using an agent-orchestrated pipeline combining video understanding, retrieval-augmented generation (RAG), and conversational memory. Deployed as a FastAPI backend with a React frontend on Google Cloud Run.

## What It Does

Upload a video of your workout and get detailed, expert-backed form feedback. The system extracts frames from your video, classifies the exercise, retrieves relevant coaching knowledge, and uses multi-frame analysis to identify form issues across your full range of motion. You can also send text questions, voice questions (transcribed via Whisper), or just have a follow-up conversation about a previous analysis.

Responses are grounded in a curated knowledge base of fitness experts (Jeff Nippard, Mark Rippetoe, Layne Norton) — not generic LLM output. This means feedback is traceable to real sources and less prone to hallucination.

## How It Works

The entire pipeline is orchestrated as a **LangGraph state machine** ([app/graph.py](app/graph.py)). A conditional router at the entry point inspects the input and directs it down one of three paths:

```
                    ┌─────────────────────┐
                    │     User Input       │
                    │  (query +/- video)   │
                    └────────┬────────────┘
                             │
                      route_query()
                     ┌───────┼────────────┐
                     │       │            │
                     ▼       ▼            ▼
              ┌──────────┐ ┌──────────┐ ┌──────────┐
              │  Video   │ │ Vector   │ │  Chat    │
              │ Encoder  │ │ DB Node  │ │ Memory   │
              └────┬─────┘ └────┬─────┘ └────┬─────┘
                   ▼            │             │
              ┌──────────┐     │             │
              │ Video    │     │             │
              │ Classify │     │             │
              └────┬─────┘     │             │
                   ▼            │             │
              ┌──────────┐     │             │
              │ Vector   │     │             │
              │ DB Node  │     │             │
              └────┬─────┘     │             │
                   ▼            ▼             │
              ┌──────────┐ ┌──────────┐      │
              │ Response │ │ Response │      │
              │Generator │ │Generator │      │
              └────┬─────┘ └────┬─────┘      │
                   │            │             │
                   └────────────┴─────────────┘
                                │
                               END
```

### Video Path (video attached)
1. **Video Encoder** — [app/video_processing.py](app/video_processing.py) extracts frames from the workout video using OpenCV and base64-encodes them
2. **Video Classification** — GPT-5.4-nano identifies the exercise type and key body checkpoints from a representative frame
3. **Vector DB** — Classification keywords + user query both drive similarity searches against ChromaDB; results are deduplicated
4. **Response Generator** — All frames + retrieved expert context are passed to GPT-5.4 for multi-frame form analysis with conversation history. The full response is streamed to the user, then a lightweight GPT-5.4-nano summarizer condenses it into a short memory entry before it is written to chat history — this keeps follow-up context small and cheap without losing the key facts.

### Text + Vectorstore Path (exercise/technique question, no video)
1. **Vector DB** — User query drives a similarity search for relevant expert context
2. **Response Generator** — Retrieved context + conversation history are passed to GPT-5.4

### Memory-Only Path (general conversation)
1. **Chat Memory** — GPT-5.4-nano responds using conversation history alone (no retrieval)

The path is selected by `route_query()`: if a video is attached it always takes the video path; otherwise a GPT-5.4-nano router classifies the text query as needing vectorstore retrieval or memory only.

## Backend API

The FastAPI app ([app/main.py](app/main.py)) exposes:

- `GET /` — health check
- `GET /sessions` — list recent sessions for the sidebar
- `GET /sessions/{session_id}` — fetch a single session record
- `POST /analyze` — multipart endpoint accepting `user_query`, `user_video`, and/or `user_audio`. Returns a **Server-Sent Events** stream so the frontend can show progress (`Watching your video...`, classification preview, final response) as each graph node completes. Audio uploads are transcribed with the OpenAI Whisper API before being passed to the graph.

Sessions are persisted via [app/sessions.py](app/sessions.py), which currently uses a local JSON store with a stable interface (`create` / `get` / `list` / `update`) designed to be swapped for Firestore without changing call sites.

## Frontend

[frontend/](frontend/) is a React 19 + Vite single-page app that consumes the SSE `/analyze` stream, renders progress updates and the final coaching response (via `react-markdown`), and lists prior sessions in a sidebar. Uploaded videos are previewed inline in an autoplay/loop player next to the chat. It is built into a static bundle and served by nginx ([frontend/nginx.conf](frontend/nginx.conf)) in its own container.

## Deployment

Both services run on **Google Cloud Run**, built via Cloud Build:

- **Backend** — [dockerfile](dockerfile) + [cloudbuild.yaml](cloudbuild.yaml) build the FastAPI image and push to Artifact Registry (`europe-west1`)
- **Frontend** — [frontend/dockerfile](frontend/dockerfile) builds the Vite bundle and serves it with nginx
- The persisted ChromaDB index is bundled into the backend image so retrieval works without any external vector DB

## Tech Stack

- **Python / FastAPI** — async backend with SSE streaming
- **React 19 + Vite** — frontend SPA
- **LangGraph** — state machine orchestration with conditional routing
- **OpenAI API** — GPT-5.4 (form analysis), GPT-5.4-nano (query routing, image classification, memory summarization, memory-only chat), `text-embedding-3-small` (embeddings), Whisper (voice-to-text)
- **LangChain** — document loading, text splitting, prompt templates, `RunnableWithMessageHistory` for conversation memory
- **ChromaDB** — persistent vector storage and similarity search
- **OpenCV** — video frame extraction and processing
- **Google Cloud Run + Cloud Build + Artifact Registry** — container hosting and CI
- **LangSmith** — tracing and evaluation

## Evaluation

- **LangSmith** — RAG baseline evaluated across correctness, latency (P50/P99), token usage, and cost. Eval scripts and datasets live in [llm-evals/](llm-evals/).

## Key Design Decisions

- **Streaming responses**: The `/analyze` endpoint emits SSE events as each graph node finishes, so the user sees `Watching your video...` → classification preview → final response instead of waiting on a single blocking request.
- **Multi-frame analysis**: Rather than analyzing a single snapshot, the system passes multiple frames to GPT-5 so it can detect patterns across the movement (e.g., bar path, elbow flare throughout the rep).
- **Classifier-driven retrieval**: A separate classification model tags each image with exercise type and body checkpoints, which are then used as the similarity search query. This produces more relevant context than raw image descriptions.
- **Summarized chat memory**: After each video analysis, a small model condenses the full response into a short memory entry (exercise, main issues, priority fixes) before it's written to history. This cut per-turn memory from ~18K to ~1.4K tokens and dropped chat-memory-path latency accordingly, without losing continuity for follow-ups.
- **Precision over recall**: For fitness advice, wrong information can cause injury. The system is designed to say "I don't have that information yet" rather than guess.
- **Grounded responses**: The system prompt explicitly constrains the LLM to only use retrieved context, reducing hallucination risk.
- **Pluggable session storage**: Sessions go through a thin interface so the JSON-file backend can be swapped for Firestore without touching the API or graph code.
- **LangGraph state machine**: Explicit, inspectable control flow with typed state (`GraphState`) makes routing logic and data dependencies clear and extensible.

## Project Structure

```
fitness-form-coach/
├── app/                              # FastAPI backend
│   ├── main.py                       # API routes, SSE streaming, audio transcription
│   ├── graph.py                      # LangGraph state machine: nodes, routing, execution
│   ├── video_processing.py           # Video frame extraction + base64 encoding
│   ├── chat_memory.py                # Per-session conversation history
│   └── sessions.py                   # Session persistence (JSON store, Firestore-ready)
├── frontend/                         # React 19 + Vite SPA
│   ├── src/                          # Components, SSE client, session UI
│   ├── nginx.conf                    # Static serving config for Cloud Run
│   └── dockerfile
├── chroma_db/                        # Persisted ChromaDB vector store (bundled into image)
├── data/
│   ├── articles/                     # Reference materials (PDFs)
│   ├── processed/                    # Cleaned transcript chunks with metadata
│   ├── raw_workout_videos/           # Source workout videos
│   └── transcripts/                  # Raw transcript JSON files
├── notebooks/
│   ├── vectorstore_setup.py          # Transcript fetching, cleaning, chunking, vectorstore helpers
│   ├── vectorstore_setup.ipynb       # Vectorstore creation and document ingestion
│   ├── youtube_transcripts.ipynb     # YouTube transcript fetching & cleaning
│   ├── text_transcripts.ipynb        # PDF text processing
│   └── test_graph.ipynb              # Graph experimentation
├── llm-evals/                        # LangSmith evaluation scripts and datasets
├── prompts/                          # Prompt development notes
├── main.py                           # Uvicorn entrypoint (re-exports app.main:app)
├── dockerfile                        # Backend container
├── cloudbuild.yaml                   # Cloud Build pipeline
├── requirements.txt                  # Dev dependencies
├── requirements-prod.txt             # Production dependencies
└── README.md
```

## Running Locally

```bash
# Backend
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

You'll need an `.env` with `OPENAI_API_KEY` and `LANGSMITH_API_KEY`. The backend reads `CHROMA_DIR` (defaults to `./chroma_db`).

## What's Next

- Swap the JSON session store for Firestore
- Move uploaded videos to GCS instead of `tempfile`
- Expanded evaluation benchmarks using LangSmith experiments
- Expanded exercise dataset and expert sources
- Fine-tuned retrieval strategies (chunking, top-k tuning)

## Author

Chandler Shortlidge
[LinkedIn](https://linkedin.com/in/chandlershortlidge) | [GitHub](https://github.com/chandlershortlidge)

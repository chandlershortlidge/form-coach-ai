# FormCoach AI

A multimodal AI coaching system that analyzes workout videos and user queries using an agent-orchestrated pipeline combining video understanding, retrieval-augmented generation (RAG), and conversational memory.

## What It Does

Upload a video of your workout and get detailed, expert-backed form feedback. The system extracts frames from your video, classifies the exercise, retrieves relevant coaching knowledge, and uses multi-frame analysis to identify form issues across your full range of motion.

Responses are grounded in a curated knowledge base of fitness experts (Jeff Nippard, Mark Rippetoe, Layne Norton) — not generic LLM output. This means feedback is traceable to real sources and less prone to hallucination.

## How It Works

The entire pipeline is orchestrated as a **LangGraph state machine** (`create_graph.ipynb`). A conditional router at the entry point inspects the input and directs it down one of three paths:

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
1. **Video Encoder** — `video_processing.py` extracts frames from the workout video using OpenCV and base64-encodes them
2. **Video Classification** — GPT-4o identifies the exercise type and key body checkpoints from a representative frame
3. **Vector DB** — Classification keywords + user query both drive similarity searches against ChromaDB; results are deduplicated
4. **Response Generator** — All frames + retrieved expert context are passed to GPT-5 for multi-frame form analysis with conversation history

### Text + Vectorstore Path (exercise/technique question, no video)
1. **Vector DB** — User query drives a similarity search for relevant expert context
2. **Response Generator** — Retrieved context + conversation history are passed to GPT-5

### Memory-Only Path (general conversation)
1. **Chat Memory** — GPT-5 responds using conversation history alone (no retrieval)

The path is selected by `route_query()`: if a video is attached it always takes the video path; otherwise a GPT-4o router classifies the text query as needing vectorstore retrieval or memory only.

## Tech Stack

- **Python**
- **LangGraph** — state machine orchestration with conditional routing
- **OpenAI API** — GPT-5 (form analysis + conversation), GPT-4o (image classification + query routing), `text-embedding-3-small` (embeddings)
- **LangChain** — document loading, text splitting, prompt templates, `RunnableWithMessageHistory` for conversation memory
- **ChromaDB** — persistent vector storage and similarity search
- **OpenCV** — video frame extraction and processing
- **OpenAI Whisper API** — voice-to-text input for hands-free querying

## Evaluation
- **LangSmith** - RAG baseline evaluated across correctness, latency (P50/P99), token usage, and cost

## Key Design Decisions

- **Multi-frame analysis**: Rather than analyzing a single snapshot, the system passes multiple frames to GPT-5 so it can detect patterns across the movement (e.g., bar path, elbow flare throughout the rep).
- **Classifier-driven retrieval**: A separate classification model tags each image with exercise type and body checkpoints, which are then used as the similarity search query. This produces more relevant context than raw image descriptions.
- **Precision over recall**: For fitness advice, wrong information can cause injury. The system is designed to say "I don't have that information yet" rather than guess.
- **Grounded responses**: The system prompt explicitly constrains the LLM to only use retrieved context, reducing hallucination risk.
- **Metadata tagging**: Each chunk carries author, difficulty level, and exercise type — enabling future filtering by user experience level.
- **LangGraph state machine**: Explicit, inspectable control flow with typed state (`GraphState`) makes routing logic and data dependencies clear and extensible.

## Project Structure

```
fitness-form-coach/
├── chroma_db/                        # Persisted ChromaDB vector store
├── data/
│   ├── articles/                     # Additional reference materials (PDFs)
│   ├── processed/
│   │   ├── processed-images/         # Extracted video frames (JPG)
│   │   └── cleaned_*.json            # Cleaned transcript chunks with metadata
│   ├── raw_workout_videos/           # Source workout videos
│   └── transcripts/                  # Raw transcript JSON files
├── notebooks/
│   ├── video_processing.py           # Video frame extraction + base64 encoding
│   ├── vectorstore_setup.py          # Transcript fetching, cleaning, chunking, metadata, and vectorstore helpers
│   ├── chat_memory.py                # Per-session conversation history management
│   ├── utils.py                      # JSON I/O helpers
│   ├── create_graph.ipynb            # LangGraph agent: state, nodes, routing, and execution
│   ├── vectorstore_setup.ipynb       # Vectorstore creation and document ingestion
│   ├── youtube_transcripts.ipynb     # YouTube transcript fetching & cleaning
│   └── text_transcripts.ipynb        # PDF text processing
├── prompts/
│   └── vision_model_prompts.md       # Vision model prompt development & examples
├── .gitignore
├── README.md
└── requirements.txt
```

## What's Next

- Expanded evaluation benchmarks using LangSmith experiments
- Streamlit or FastAPI interface for real-time interaction
- Expanded exercise dataset and expert sources
- Fine-tuned retrieval strategies (chunking, top-k tuning)

## Author

Chandler Shortlidge
[LinkedIn](https://linkedin.com/in/chandlershortlidge) | [GitHub](https://github.com/chandlershortlidge)

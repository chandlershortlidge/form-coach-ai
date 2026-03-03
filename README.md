# Fitness Form Coach

A RAG-powered AI coaching system that analyzes workout videos and provides personalized exercise form feedback grounded in expert fitness knowledge.

## What It Does

Upload a video of your workout and get detailed, expert-backed form feedback. The system extracts frames from your video, classifies the exercise, retrieves relevant coaching knowledge, and uses multi-frame analysis to identify form issues across your full range of motion.

Responses are grounded in a curated knowledge base of fitness experts (Jeff Nippard, Mark Rippetoe, Layne Norton) — not generic LLM output. This means feedback is traceable to real sources and less prone to hallucination.

## How It Works

### Video Analysis Pipeline

1. **Extract** — `video_processing.py` extracts frames from workout videos at calculated intervals using OpenCV and base64-encodes them for API transmission
2. **Classify** — A GPT-4o classifier identifies the exercise type and key body checkpoints from a representative frame
3. **Retrieve** — Classification tags + the user's text query both drive similarity searches against ChromaDB; results are deduplicated to build a focused context window
4. **Analyze** — All extracted frames + retrieved expert context are passed to GPT-5 for multi-frame form analysis across the full range of motion
5. **Respond** — `chat_memory.py` maintains per-session conversation history so follow-up questions retain context

### Text Q&A Pipeline

A query router (`router.ipynb`) classifies user input as either:
- **memory only** — general conversation handled with chat history alone
- **vectorstore & memory** — exercise/technique questions that trigger a similarity search for grounded expert context before responding

Both pipelines share the same retrieval layer (`rag_pipeline.py`) and conversation memory.

## Tech Stack

- **Python**
- **OpenAI API** — GPT-5 (multi-frame form analysis + transcript cleaning), GPT-4o (image classification + query routing), `text-embedding-3-small` (embeddings)
- **LangChain** — document loading, text splitting, prompt templates, chains, `RunnableWithMessageHistory` for conversation memory
- **ChromaDB** — persistent vector storage and similarity search
- **OpenCV** — video frame extraction and processing
- **LangGraph** — state machine orchestration (in progress, see below)

## Key Design Decisions

- **Multi-frame analysis**: Rather than analyzing a single snapshot, the system passes multiple frames to GPT-5 so it can detect patterns across the movement (e.g., bar path, elbow flare throughout the rep).
- **Classifier-driven retrieval**: A separate classification model tags each image with exercise type and body checkpoints, which are then used as the similarity search query. This produces more relevant context than raw image descriptions.
- **Precision over recall**: For fitness advice, wrong information can cause injury. The system is designed to say "I don't have that information yet" rather than guess.
- **Grounded responses**: The system prompt explicitly constrains the LLM to only use retrieved context, reducing hallucination risk.
- **Metadata tagging**: Each chunk carries author, difficulty level, and exercise type — enabling future filtering by user experience level.

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
│   ├── rag_pipeline.py               # Core RAG: chunking, embedding, metadata, retrieval
│   ├── video_processing.py           # Video frame extraction + base64 encoding
│   ├── chat_memory.py                # Per-session conversation history management
│   ├── utils.py                      # JSON I/O helpers
│   ├── router.py                     # Query router (placeholder, logic in router.ipynb)
│   ├── rag_pipeline.ipynb            # Main pipeline: classify → retrieve → analyze → respond
│   ├── router.ipynb                  # Text query routing (memory vs. vectorstore)
│   ├── create_graph.ipynb            # LangGraph refactor (in progress)
│   ├── video_pipeline.ipynb          # Video frame extraction workflow
│   ├── chat_memory.ipynb             # Conversation history testing
│   ├── youtube_transcripts.ipynb     # YouTube transcript fetching & cleaning
│   └── text_transcripts.ipynb        # PDF text processing
├── prompts/
│   └── vision_model_prompts.md       # Vision model prompt development & examples
├── .gitignore
├── README.md
└── requirements.txt
```

## LangGraph Refactor (In Progress)

The current pipeline orchestration lives in `rag_pipeline.ipynb` as a single function. A refactor to **LangGraph** is underway (`create_graph.ipynb`) to replace this with a stateful graph that makes the flow explicit and extensible:

```
┌─────────────────────┐
│   User Input        │
│  (query + video)    │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Video Classification│  ← GPT-4o: exercise type + body checkpoints
│       Node          │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Vector DB Node     │  ← ChromaDB similarity search (query + classification)
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Response Generator │  ← GPT-5: multi-frame analysis with retrieved context
│       Node          │
└─────────────────────┘
```

**Status:** The `GraphState` schema and node stubs are defined. Node implementations are being migrated from the monolithic pipeline function. The query router will be integrated as a conditional edge to handle video vs. text-only inputs.

## What's Next

- Complete LangGraph migration with conditional routing
- Voice-to-text input (Whisper API)
- Evaluation framework (retrieval quality + response grounding)
- Streamlit frontend
- More exercise types and expert sources

## Author

Chandler Shortlidge
[LinkedIn](https://linkedin.com/in/chandlershortlidge) | [GitHub](https://github.com/chandlershortlidge)

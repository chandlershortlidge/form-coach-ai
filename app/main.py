
import logging
from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import tempfile
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__) 

if __package__:
    from .graph import (
        app as graph_app, transcribe_audio,
        video_encoder_node, video_classification_node,
        vector_db_node, response_generator,
    )
    from .sessions import create_session, get_session, update_session, list_sessions
else:
    from graph import (
        app as graph_app, transcribe_audio,
        video_encoder_node, video_classification_node,
        vector_db_node, response_generator,
    )
    from sessions import create_session, get_session, update_session, list_sessions

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# health check

@app.get("/")
def health_check():
    return {"status": "running"}


# ── Session endpoints ──

@app.get("/sessions")
def api_list_sessions(limit: int = 20):
    return list_sessions(limit=limit)


@app.get("/sessions/{session_id}")
def api_get_session(session_id: str):
    session = get_session(session_id)
    if not session:
        return {"error": "not found"}, 404
    return session


@app.post("/analyze")
async def analyze(session_id: str, user_query: str = Form(None), user_video: UploadFile = None, user_audio: UploadFile = None):
    logger.info(f"analyze request started | session_id={session_id}")

    #1. if audio, transcribe it to get the query
    transcription = None
    if user_audio:
        suffix = os.path.splitext(user_audio.filename)[1]
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(await user_audio.read())
            audio_path = tmp.name
            user_query = transcribe_audio(audio_path)
            transcription = user_query
            os.remove(audio_path)

    # 2. if video, save it

    video_path = None
    video_filename = None
    if user_video:
        video_filename = user_video.filename
        suffix = os.path.splitext(video_filename)[1]
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(await user_video.read())
            video_path = tmp.name

    # 3. create a persistent session record
    create_session(
        session_id,
        user_query=user_query,
        video_filename=video_filename,
    )
    update_session(session_id, status="analyzing")

    async def event_stream():
        nonlocal user_query

        if video_path:
            # Step 1: Encode video frames
            yield f"data: {json.dumps({'type': 'status', 'message': 'Watching your video...'})}\n\n"

            encoder_result = await asyncio.to_thread(video_encoder_node, {"user_video": video_path})

            # Step 2: Classify exercise
            classification_result = await asyncio.to_thread(
                video_classification_node,
                {"classification_image": encoder_result["classification_image"]},
            )

            classification_raw = classification_result.get('classification_raw', '')
            # Derive a label from the first line of classification (exercise name)
            exercise_label = classification_raw.split('\n')[0].strip().replace('*', '') if classification_raw else video_filename
            update_session(session_id, classification_raw=classification_raw, exercise_label=exercise_label)

            # Send raw classification text to frontend for display
            yield f"data: {json.dumps({'type': 'preview', 'classification_raw': classification_raw})}\n\n"

            # Step 3: Retrieval + response generation
            yield f"data: {json.dumps({'type': 'status', 'message': 'Putting your coaching notes together...'})}\n\n"

            state = {
                "session_id": session_id,
                "user_query": user_query or "Analyze my form",
                "user_video": video_path,
                "classified_keywords": classification_result["classified_keywords"],
                "encoded_images": encoder_result["encoded_images"],
                "classification_image": encoder_result["classification_image"],
            }
            retrieval_result = await asyncio.to_thread(vector_db_node, state)
            state = {**state, **retrieval_result}
            response_result = await asyncio.to_thread(response_generator, state)
            state = {**state, **response_result}

            if video_path:
                os.remove(video_path)

            update_session(session_id, response=state['response'], status="completed")
            yield f"data: {json.dumps({'type': 'response', 'response': state['response'], 'transcription': transcription})}\n\n"

        else:
            # Text-only or audio path — run the full graph
            result = await asyncio.to_thread(
                graph_app.invoke,
                {"session_id": session_id, "user_query": user_query, "user_video": ""},
            )

            update_session(session_id, response=result['response'], status="completed",
                           exercise_label=user_query[:50] if user_query else "Text analysis")
            yield f"data: {json.dumps({'type': 'response', 'response': result['response'], 'transcription': transcription})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

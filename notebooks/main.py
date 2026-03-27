from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
if __package__:
    from .graph import (
        app as graph_app, transcribe_audio,
        video_encoder_node, video_classification_node,
        vector_db_node, response_generator,
    )
else:
    from graph import (
        app as graph_app, transcribe_audio,
        video_encoder_node, video_classification_node,
        vector_db_node, response_generator,
    )
import asyncio
import json
import tempfile
import os

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
# a GET endpoint that returns a simple message to confirm the server is running:

@app.post("/analyze")
async def analyze(session_id: str, user_query: str = Form(None), user_video: UploadFile = None, user_audio: UploadFile = None):

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
    if user_video:
        suffix = os.path.splitext(user_video.filename)[1]
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(await user_video.read())
            video_path = tmp.name

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

            # Send raw classification text to frontend for display
            yield f"data: {json.dumps({'type': 'preview', 'classification_raw': classification_result.get('classification_raw', '')})}\n\n"

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

            yield f"data: {json.dumps({'type': 'response', 'response': state['response'], 'transcription': transcription})}\n\n"

        else:
            # Text-only or audio path — run the full graph
            result = await asyncio.to_thread(
                graph_app.invoke,
                {"session_id": session_id, "user_query": user_query, "user_video": ""},
            )

            yield f"data: {json.dumps({'type': 'response', 'response': result['response'], 'transcription': transcription})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from graph import app as graph_app, transcribe_audio
from video_processing import analyze_video
from langchain_openai import ChatOpenAI
import re
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


    #3. invoke the graph

    result = graph_app.invoke({
        "session_id": session_id,
        "user_query": user_query,
        "user_video": video_path or ""
    })
    
    #4. clean up 

    if video_path:
        os.remove(video_path)
    print(result["response"])

    return {"response": result["response"], "transcription": transcription}


@app.post("/preview")
async def preview(session_id: str, user_video: UploadFile = File(...)):
    # 1. Save video to temp file
    suffix = os.path.splitext(user_video.filename)[1]
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await user_video.read())
        video_path = tmp.name

    # 2. Extract frames and get the first frame for classification
    frames = analyze_video(filepath_in=video_path, frame_count=1, max_seconds=10)
    classification_image = frames[0]

    # 3. Run GPT-4o classification on first frame
    router_llm = ChatOpenAI(model='gpt-4o')
    response = router_llm.invoke([
        {"role": "user", "content": [
            {"type": "text", "text": """Your job is to analyze images of users working out for proper form, and list the key checkpoints of their to body evaluate.
    Give me ONLY the bodypart checkpoints. Do NOT include evaluation suggestions. Do NOT include an intro sentence.
    Output format should be exactly the example below.
    **Example**
    Overhead press

    1. Feet & base
    2. Glutes & legs
    3. Core & Ribcage
    4. Shoulder position
    5. Bar path
    6. Head & Neck
    7. Lockout position
    8. Tempo and control
    """},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{classification_image}"}}
        ]}
    ])

    # 4. Parse response into exercise name + checklist
    raw_text = response.content.strip()
    lines = [line.strip() for line in raw_text.split('\n') if line.strip()]

    exercise = lines[0] if lines else "Unknown exercise"
    checklist = []
    for line in lines[1:]:
        item = re.sub(r'^\d+[\.\)]\s*', '', line)
        if item:
            checklist.append(item)

    # 5. Clean up
    os.remove(video_path)

    return {"exercise": exercise, "checklist": checklist}

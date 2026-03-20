from fastapi import FastAPI, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from graph import app as graph_app, transcribe_audio
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
   
   # what are the main musles involved in a bench press?

from fastapi import FastAPI, UploadFile, File
from graph import app as graph_app, transcribe_audio
import tempfile
import os 

app = FastAPI()

# health check 

@app.get("/")
def health_check():
    return {"status": "running"}
# a GET endpoint that returns a simple message to confirm the server is running:

@app.post("/analyze")
async def analyze(session_id: str, user_query: str, user_video: UploadFile = None, user_audio: UploadFile = None):
# save to temp file because user_video expects a filepath
 # .delete=False means "don't delete this file when we're done writing" because we still need it for the pipeline.
    if user_video:
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp.write(await user_video.read())
            tmp_path = tmp.name

        result = graph_app.invoke({
            "session_id": session_id,
            "user_query": user_query,
            "user_video": tmp_path
        })
        os.remove(tmp_path)
        return {"response": result["response"]}
        
    if user_audio:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp.write(await user_audio.read())
            tmp_path = tmp.name
            user_query = transcribe_audio(tmp_path)

            result = graph_app.invoke({
            "session_id": session_id,
            "user_query": user_query,
            "user_video": None
        })
        os.remove(tmp_path)
        return {"response": result["response"]}

    if user_video == None:
        result = graph_app.invoke({
        "session_id": session_id,
        "user_query": user_query,
        "user_video": None
    })
    return {"response": result["response"]}
   
   # what are the main musles involved in a bench press?
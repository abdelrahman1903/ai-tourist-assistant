from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from model import Model  # Ensure you have a Model class defined in model.py
from Whisper import Whisper
import os
import shutil
from pydub import AudioSegment
from RAG.Chunking import Chunking
import json

app = FastAPI()
model_instance = Model()  # Instantiate the model
whisper_instance = Whisper()
# Allow frontend to access backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define request body structure
class TextRequest(BaseModel):
    text: str

@app.get("/")
def read_root():
    return {"message": "FastAPI is running!"}

@app.post("/chat")  # ✅ Change to POST
async def chat(request: Request):
    data = await request.json()
    user_text = data.get("text")
    location = data.get("location")
    response = model_instance.generate_response(user_text,location)
    # print("response",response)
    return {"response": response}  # ✅ Ensure the correct response field

@app.post("/audio")  # ✅ Change to POST
async def chat(audio: UploadFile = File(...)):
    input_path = "temp_input.webm"  # Save raw uploaded file
    wav_path = "temp_audio.wav"     # Will convert to this
    # with open("temp_audio.wav", "wb") as f:
    #     content = await audio.read()
    #     f.write(content)
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(audio.file, buffer)
    # print(audio)
    # user_Audio = audio
    # Convert using pydub (requires ffmpeg)
    audio_segment = AudioSegment.from_file(input_path)
    audio_segment = audio_segment.set_frame_rate(16000).set_channels(1)  # Ensure 16kHz mono for Whisper
    audio_segment.export(wav_path, format="wav")
    response = whisper_instance.generate_response("temp_audio.wav")
    os.remove(input_path)
    os.remove(wav_path)
    return {"Transcription": response}  # ✅ Ensure the correct response field

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), message: str = Form(...)):
    with open(f"uploads/{file.filename}", "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    parsed_message = json.loads(message)
    response = Chunking.LLM_Response(parsed_message,f"uploads/{file.filename}")    
    return {"response": response}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

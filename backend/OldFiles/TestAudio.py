# from openai import OpenAI
# from dotenv import load_dotenv
# import os

# load_dotenv()
# api_key = os.getenv("OPENROUTER_API_KEY")

# audio_file = open("C:\backup\guc\bachelor\backend\audio.mp3", "rb")  # Load your audio file

# client = OpenAI(
#     base_url="https://openrouter.ai/api/v1",
#     api_key=api_key,  # Use environment variable instead of hardcoded key
# )

# response = client.audio.transcriptions.create(
#     model="whisper-1",  # Use OpenAI's Whisper model
#     file=audio_file,
#     response_format="text",  # Can also use "json" for structured output
# )

# print(response)  # This prints the transcribed text


import livekit
import asyncio

from dotenv import load_dotenv
import os


load_dotenv()
LIVEKIT_URL = os.getenv("LIVEKIT_URL")
API_KEY = os.getenv("LIVEKIT_API_KEY")
API_SECRET = os.getenv("LIVEKIT_API_SECRET")


async def transcribe_file(audio_file):
    client = livekit.Client(LIVEKIT_URL, API_KEY, API_SECRET)
    with open("C:\\backup\\guc\\bachelor\\backend\\audio.mp3", "rb") as file:
        audio_data = file.read()

    transcript = await client.transcribe(audio_data)
    print("Transcription:", transcript)

asyncio.run(transcribe_file("audio.mp3"))

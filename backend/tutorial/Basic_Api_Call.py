import google.generativeai as genai
import os
from dotenv import load_dotenv

#getting the api_key form the .env file(to avoid key exposure)
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

#initialization of LLM Model
messages = [
    {"role": "user", "parts": ["You are a kind helpful assistant."]},
]
if not api_key:
    raise ValueError("Missing OPENROUTER_API_KEY. Did you forget to set it in your .env file?")
genai.configure(api_key=api_key)
LLMmodel = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
)

#api call to contact LLM api via terminal
while True:
    #takes user's input as string
    message = input("User : ")

    if message:
        #user's message is added to messages array
        messages.append(
            {"role": "user", "parts": [message]},
        )

        #contacting the LLM api
        response = LLMmodel.generate_content(messages)

        #getting the response that the LLM sent
        reply = response.text
        #print reply in the terminal
        print(f"ChatGPT : {reply}")
        #the reply is added to the messages array so that the model could keep context and remember the previous messagges
        messages.append({"role": "model", "parts": [reply]})
i
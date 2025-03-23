from openai import OpenAI

import os
from dotenv import load_dotenv

#getting the api_key form the .env file(to avoid key exposure)
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

#initialization of LLM Model
messages = [
    {"role": "system", "content": "You are a kind helpful assistant."},
]
if not api_key:
    raise ValueError("Missing OPENROUTER_API_KEY. Did you forget to set it in your .env file?")
client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=api_key,
)

#api call to contact LLM api via terminal
while True:
    #takes user's input as string
    message = input("User : ")

    if message:
        #user's message is added to messages array
        messages.append(
            {"role": "user", "content": message},
        )
        #contacting the LLM api
        chat = client.chat.completions.create(
            model="google/gemini-2.0-pro-exp-02-05:free",
            messages=messages
            )
        #getting the response that the LLM sent
        reply = chat.choices[0].message.content
        #print reply in the terminal
        print(f"ChatGPT : {reply}")
        #the reply is added to the messages array so that the model could keep context and remember the previous messagges
        messages.append({"role": "assistant", "content": reply})
i
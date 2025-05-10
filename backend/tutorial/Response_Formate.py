import google.generativeai as genai

import os
from dotenv import load_dotenv

from pydantic import BaseModel, Field

#getting the api_key form the .env file(to avoid key exposure)
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

#defining the response format that we want the model to stick to, and a discribtion of what each field is for
class CalenderEvent(BaseModel):
    participants: list[str] = Field(description="Lists the pepole participating in the event")
    date: str
    location: str =  Field(description="location of the event")
    notes: str = Field(description="Any further notes or text the model provides")


class Response_Formate:
    #initialization of LLM Model
    if not api_key:
      raise ValueError("Missing OPENROUTER_API_KEY. Did you forget to set it in your .env file?")
    def __init__(self):
        genai.configure(api_key=api_key)
        self.LLMmodel = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
        )
        self.messages = [{"role": "user", "parts": ["You are a kind, helpful culture assistant."]}]


    #this function is the one used gt generate the response to the user's message
    def generate_response(self, user_message):
       
        self.messages.append({"role": "user", "parts": [user_message]})

        response = self.LLMmodel.generate_content(
            contents = self.messages,
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": CalenderEvent,
                "temperature": 0,
            }
        )

        #getting the response that the LLM sent
        reply = response.text
        #the reply is added to the messages array so that the model could keep context and remember the previous messagges
        self.messages.append({"role": "model", "parts": [reply]})
        return reply


#for testing if you want to run the file directly instead of running FastApi.py
response_format__instance = Response_Formate()
while(True):
    userInput = input()
    print(response_format__instance.generate_response(userInput))
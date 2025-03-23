from openai import OpenAI

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
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        self.messages = [{"role": "system", "content": "You are a kind, helpful culture assistant."}]


    #this function is the one used gt generate the response to the user's message
    def generate_response(self, user_message):
       
        self.messages.append({"role": "user", "content": user_message})

        chat = self.client.beta.chat.completions.parse(
            model="google/gemini-2.0-pro-exp-02-05:free",
            messages=self.messages,
            response_format = CalenderEvent, #gives the model the response format that we created
        )

        #getting the response that the LLM sent
        reply_message = chat.choices[0].message
        reply = reply_message.content
        #the reply is added to the messages array so that the model could keep context and remember the previous messagges
        self.messages.append({"role": "assistant", "content": reply})
        return reply



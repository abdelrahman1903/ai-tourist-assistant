from openai import OpenAI
from pydantic import BaseModel, Field
from GeographicAwarness import GeographicAwarness
from Retrieval import Retrieval
import json
import time
from typing import List, Optional
import os

from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")
# class Museum(BaseModel):
#   english_name: str
#   arabic_name: Optional[str] = "N/A"
#   opening_hours: Optional[str] = "N/A"
#   museum_type: Optional[str] = "N/A"
#   wikidata: Optional[str] = "N/A"
      
# class CalendarEvent(BaseModel):
#   museums: List[Museum] 
class CalenderEvent(BaseModel):
    # flag: str
    # language: str
    museums_near_you: list[str] =  Field(description="Lists the museums in English names only")
    notes: str = Field(description="Any further notes or text the model provides")
class Model:
    if not api_key:
      raise ValueError("Missing OPENROUTER_API_KEY. Did you forget to set it in your .env file?")
    def __init__(self):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,  # Use environment variable instead of hardcoded key
        )
        self.messages = [{"role": "system", "content": "You are a kind, helpful culture assistant."}]

    #Define a tool for geographic awarness
    tools=[
    {
      "type": "function",
      "function": {
        "name": "nearby_museums",
        "description": "Get museums locations around the user based on current location",
        "parameters": {
          "type": "object",
          "properties": {
            "dummy": {  # Placeholder field
                        "type": "boolean",
                        "description": "This is a placeholder and should be ignored"
                    }
          },
          "required": []
        },
        # "strict":True,
      }
    },
    {
        "type": "function",
        "function": {
            "name": "search_DB",
            "description": "get model info, like its base location and its use",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                },
                "required": ["question"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
  ]

    def generate_response(self, user_message):
       
        self.messages.append({"role": "user", "content": user_message})

        chat = self.client.chat.completions.create(
            model="google/gemini-2.0-pro-exp-02-05:free",
            messages=self.messages,
            tools=self.tools  # Pass tools to allow function calling
        )
        # chat = self.client.beta.chat.completions.parse(
        #     model="google/gemini-2.0-pro-exp-02-05:free",
        #     messages=self.messages,
        #     response_format = self.CalenderEvent,
        #     # tools=self.tools,
        # )
        reply_message = chat.choices[0].message

        def call_function(name, args):
          if name == "search_DB":
            return Retrieval.search_db(**args)
          elif name == "nearby_museums" :
            return GeographicAwarness.nearLocations()

        if reply_message.tool_calls:
            for tool_call in reply_message.tool_calls:
                    name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments)
                    self.messages.append(chat.choices[0].message)

                    result = call_function(name,args)
                
                    self.messages.append(
                        {"role": "tool", "tool_call_id": tool_call.id, "content": json.dumps(result)}
                    )

                    self.messages.append({
                      "role": "system",
                      "content": (
                          "Now respond strictly in this JSON format:\n"
                          '{\n  "museums_near_you": [<list of English museum names>],\n'
                          '  "notes": "<any additional notes>"\n}\n'
                          "Do not include anything else before or after this JSON."
                          )
                      })

                    chat2 = self.client.chat.completions.create(
                        model="google/gemini-2.0-pro-exp-02-05:free",
                        messages=self.messages,
                        # response_format = self.CalenderEvent,
                        # tools=self.tools  # Pass tools to allow function calling
                    )
                    raw_response = chat2.choices[0].message.content
                    print(f"raw_response: "+raw_response)
                    print(f"messages: "+str(self.messages))
                    try:
                      # Parse response into dict
                      parsed_json = json.loads(raw_response)
                      event = CalenderEvent(**parsed_json)
                      print(f"[Parsed Model]: {event}")
                      reply = json.dumps(event.dict(), indent=2)
                    except Exception as e:
                        print(f"[Parse Error]: {e}")
                        reply = raw_response  # fallback: show raw model response

                    self.messages.append({"role": "assistant", "content": reply})
                    return reply

        reply = reply_message.content
        self.messages.append({"role": "assistant", "content": reply})
        return reply


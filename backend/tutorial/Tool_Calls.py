import google.generativeai as genai
from google.generativeai.types import FunctionDeclaration, Tool
from pydantic import BaseModel, Field

from GeographicAwarness import GeographicAwarness
import json

import os
from dotenv import load_dotenv

import re

#getting the api_key form the .env file(to avoid key exposure)
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

#defining the response format that we want the model to stick to, and a discribtion of what each field is for
class Museums(BaseModel):
    museums_near_you: list[str] =  Field(description="Lists the museums in English names only")
    notes: str = Field(description="Any further notes or text the model provides")


class Tool_Calls:
    #initialization of LLM Model
    if not api_key:
      raise ValueError("Missing OPENROUTER_API_KEY. Did you forget to set it in your .env file?")
    def __init__(self):
        genai.configure(api_key=api_key)
        self.LLMmodel = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
        )
        self.messages = [{"role": "user", "parts": ["You are a kind, helpful culture assistant."]}]
        museums_nearby = {
            "name": "nearby_museums",
            "description": "Get museums locations around the user based on current location",
            "parameters": {
                "type": "object",
                "properties": {
                    "dummy": { 
                        # Placeholder field
                        "type": "boolean",
                        "description": "This is a placeholder and should be ignored"
                    }
                },
                "required": [],
            },
        }
        self.tools = [
            Tool(function_declarations=[museums_nearby])
        ]

    #this extarcts the json object from the response message retruned by the model
    def extract_json_from_text(self,text):
      try:
          json_str = text.strip()
          if json_str.startswith("```json"):
              json_str = re.sub(r"```json|```", "", json_str).strip()
          elif json_str.startswith("```"):
              json_str = json_str.strip("```").strip()
          return json.loads(json_str)
      except Exception as e:
          print("[Safe JSON Parse Error]", e)
          return None 

        #this function is the one used gt generate the response to the user's message
    def generate_response(self, user_message):
       
        self.messages.append({"role": "user", "parts": [user_message]})

        response = self.LLMmodel.generate_content(
            contents = self.messages,
            tools=self.tools
        )
      
        #this function is used to difine the different tools that we have and what each function name should trigger
        def call_function(name, args):
            if name == "nearby_museums" :
                return GeographicAwarness.nearLocations()
        #this check of the response that came from the model was caused by a tool call
        if response.candidates[0].content.parts[0].function_call:
            function_call = response.candidates[0].content.parts[0].function_call
            name = function_call.name #gets the tool name that should be used
            args = function_call.args #the parameters that should be passed to the functio
            result = call_function(name,args) #call the function that this tool striggers
            #stores the response of the fuction (the tool that the model called)
            self.messages.append(
                {"role": "user", "parts": [json.dumps(result)]}
            )
            #prompt to the model to be used in the next LLM api calls.
            self.messages.append({
                "role": "user",
                "parts": (
                    ["IMPORTANT: respond strictly in this JSON format:\n"
                    '{\n  "museums_near_you": [<list of English museum names>],\n'
                    '  "notes": "<any additional notes>"\n}\n'
                    "Do not include anything else before or after this JSON. Do not explain. Just output the JSON only."]
                )
            })
            #this api call is used to format the data that came from the tool call so that it is more readable
            response = self.LLMmodel.generate_content(self.messages)
            #get the response that the LLM sent
            raw_response = response.text
            #parsing the raw response to the response format that we definned
            try:
              # Parse response into dict
              parsed_json = self.extract_json_from_text(raw_response) #this calls a fuction that extracts the json object from the row response
              # parsed_json = json.loads(raw_response) #this way causes errors as the raw respone is a mix of json object but with strings added to it
              event = Museums(**parsed_json) #parse the json to our response fromat
              # print(f"[Parsed Model]: {event}")
              reply = json.dumps(event.dict(), indent=2)
            except Exception as e:
                print(f"[Parse Error]: {e}")
                reply = raw_response  # fallback: show raw model respons
            self.messages.append({"role": "model", "reply": [reply]})
            return reply


#for testing if you want to run the file directly instead of running FastApi.py
Tool_Calls__instance = Tool_Calls()
while(True):
    userInput = input()
    print(Tool_Calls__instance.generate_response(userInput))           
            
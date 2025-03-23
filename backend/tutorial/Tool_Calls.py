from openai import OpenAI
from pydantic import BaseModel, Field

from Tool import Tool
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
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        self.messages = [{"role": "system", "content": "You are a kind, helpful culture assistant."}]


    #Define a tool for geographic awarness
    tools=[
    {
      "type": "function",
      "function": {
        "name": "nearby_museums", #the function name
        "description": "Get museums locations around the user based on current location", #description for what this funcion is used for
        "parameters": { #here ww difine any parametars that our function takes as inputs
          "type": "object",
          "properties": {
            "dummy": {  # Placeholder field: in our case the fuction don't take any input parametars, but it is a must to difine at least one parametar even if it won't be used
                        "type": "boolean",
                        "description": "This is a placeholder and should be ignored"
                    }
          },
          "required": []
        },
        "strict":True,
      }
    },
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
       
        self.messages.append({"role": "user", "content": user_message})

        chat = self.client.chat.completions.create(
            model="google/gemini-2.0-pro-exp-02-05:free",
            messages=self.messages,
            tools=self.tools  # Pass tools to allow function calling
        )

        #getting the response that the LLM sent
        reply_message = chat.choices[0].message

        #this function is used to difine the different tools that we have and what each function name should trigger
        def call_function(name, args):
          if name == "nearby_museums" :
            return Tool.nearLocations()

        #this check of the response that came from the model was caused by a tool call
        if reply_message.tool_calls:
            for tool_call in reply_message.tool_calls:
                    name = tool_call.function.name #gets the tool name that should be used
                    args = json.loads(tool_call.function.arguments) #the parameters that should be passed to the function
                    self.messages.append(chat.choices[0].message)

                    result = call_function(name,args) #call the function that this tool striggers

                    #stores the tool response to the array of messages so that the model could keep the response of the tool in history
                    self.messages.append(
                        {"role": "tool", "tool_call_id": tool_call.id, "content": json.dumps(result)}
                    )

                    #prompt to the model to be used in the next LLM api calls.
                    self.messages.append({
                      "role": "system",
                      "content": (
                          " Only for the next response, respond strictly in this JSON format:\n"
                          '{\n  "museums_near_you": [<list of English museum names>],\n'
                          '  "notes": "<any additional notes>"\n}\n'
                          "Do not include anything else before or after this JSON."
                          )
                      })
                    
                    #this api call is used to format the data that came from the tool call so that it is more readable
                    chat2 = self.client.chat.completions.create(
                        model="google/gemini-2.0-pro-exp-02-05:free",
                        messages=self.messages,
                    )
                    #this way caused error, because although it is stricly said in the prompt to response in json, the LLM model does always follow this rule
                    # chat2 = self.client.beta.chat.completions.parse(
                    #     model="google/gemini-2.0-pro-exp-02-05:free",
                    #     messages=self.messages,
                    #     response_format = Museums, #gives the model the response format that we created
                    # )

                    #get the response that the LLM sent
                    raw_response = chat2.choices[0].message.content

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
                        reply = raw_response  # fallback: show raw model response

                    self.messages.append({"role": "assistant", "content": reply})
                    return reply

        reply = reply_message.content
        self.messages.append({"role": "assistant", "content": reply})
        return reply


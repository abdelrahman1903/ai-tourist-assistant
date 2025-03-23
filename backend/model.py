from openai import OpenAI
from pydantic import BaseModel, Field
from GeographicAwarness import GeographicAwarness
from Retrieval import Retrieval
import json
import time
from typing import List, Optional
import os
from typing import Optional, Literal
from dotenv import load_dotenv
import re

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")


class nearby_museums(BaseModel):
    museums_near_you: list[str] =  Field(description="Lists the museums in English names only")
    notes: str = Field(description="Any further notes or text the model provides")

class RequestType(BaseModel):
    """Router LLM call: Determine the type of request"""

    request_type: Literal["tool_call", "direct_model_response", "cultural_question"] = Field(
        description="Type of request being made"
    )
    confidence_score: float = Field(description="Confidence score between 0 and 1")
    description: str = Field(description="Cleaned description of the request")



class CulturalFrameworkInsights(BaseModel):
    hofstede: List[str] = Field(description="List of Hofstede's dimensions relevant to the country")
    schwartz: List[str] = Field(description="List of Schwartz's cultural value orientations")
    inglehart_welzel: List[str] = Field(description="List of Inglehart-Welzel cultural values")

class CultureProfile(BaseModel):
    country: str = Field(description="Name of the country")
    summary: str = Field(description="General friendly cultural summary of the country")
    history: str = Field(description="Short historical background of the country")
    Religious_Values: str = Field( description="How important religion is in everyday life, and how it influences social and personal behavior.")
    National_Pride: str = Field( description="The level of pride people take in their country’s identity, history, and heritage.")
    Respect_for_Authority: str = Field( description="The degree to which hierarchy and leadership are culturally accepted and valued.")
    Community_and_Family_Focus: str = Field( description="Emphasis on collective decision-making, family bonds, and social interdependence.")
    Obedience_in_Upbringing: str = Field( description="Cultural expectations for children to show discipline and respect for elders.")
    Trust_in_Others: str = Field( description="Levels of interpersonal trust — whether people are generally trusting of strangers or not.")
    Uncertainty_Avoidance: str = Field( description="Preference for structure, rules, and predictability to avoid ambiguity or risk.")
    Traditional_vs_Rational_Thinking: str = Field( description="Extent to which traditions, religion, and social customs guide thinking versus rational, secular reasoning.")
    # Survival_vs_Self-Expression_Values: str = Field( description="Focus on security and stability versus creativity, self-expression, and quality of life.")
    Moral_Conservatism: str = Field( description="Societal views on issues like gender roles, homosexuality, or abortion.")
    Materialist_Orientation: str = Field( description="Priority of economic and physical security over personal development or activism.")
    Social_Etiquette: str = Field( description="Expected norms in greetings, gestures, formality, and social interactions.")
    Cultural_Interpretation: str = Field( description="How people interpret behaviors, symbols, and messages — often influenced by deeper cultural meanings.")
    Hospitality_Norms: str = Field( description="How guests and strangers are treated in homes, shops, and communities.")
    Cultural_Expression: str = Field( description="Importance of music, dance, literature, folklore, and other forms of artistic expression.")
    Culinary_Traditions: str = Field( description="Local food customs, dishes, and the role of shared meals in society.")
    Food_and_Cuisine: str = Field( description="Popular traditional foods, eating habits, and how food is culturally experienced and shared.")
    Languages: str = Field( description="The official, commonly spoken, and regional languages used in the country.")
    Traditional_Clothing: str = Field( description="Common traditional garments and their significance in cultural ceremonies or daily life.")
    Traditional_Festivals: str = Field( description="Cultural or religious festivals celebrated nationally, and their importance in society.")
    Religions: str = Field( description="Dominant religions in the country and how they shape values and societal practices.")
    Cultural_Taboos: str = Field( description="Topics, behaviors, or actions considered offensive or inappropriate in the culture.")
    Arts_and_Crafts: str = Field( description="Traditional art forms, handicrafts, and creative expressions unique to the culture.")
    Greetings_and_Communication_Styles: str = Field( description="How people typically greet, speak, express politeness, and communicate in formal or informal settings.")
    Work_Culture: str = Field( description="Cultural norms around working styles, professional behavior, punctuality, hierarchy, and communication in workplaces.")
    Working_Days_and_Hours: str = Field( description="Typical working week, working hours, weekends, and holidays observed in the country.")
    framework_insights: CulturalFrameworkInsights = Field(description="Structured cultural framework positions")




class Model:
  if not api_key:
    raise ValueError("Missing OPENROUTER_API_KEY. Did you forget to set it in your .env file?")
  def __init__(self):
      self.client = OpenAI(
          base_url="https://openrouter.ai/api/v1",
          api_key=api_key,  # Use environment variable instead of hardcoded key
      )
      self.messages = [{"role": "system", "content": "You are a kind, helpful culture assistant."}]

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
          "strict":True,
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
          
  def tool_call(self,user_message):
      try:
          chat = self.client.chat.completions.create(
              model="google/gemini-2.0-pro-exp-02-05:free",
              messages=self.messages,
              tools=self.tools  # Pass tools to allow function calling
              )
          reply_message = chat.choices[0].message
          if not hasattr(reply_message, 'tool_calls') or not reply_message.tool_calls:
              raise ValueError("Tool call predicted but not present in model response")
              
          def call_function(name, args):
              if name == "search_DB":
                  return Retrieval.search_db(**args)
              elif name == "nearby_museums" :
                  return GeographicAwarness.nearLocations()
  
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
                    "IMPORTANT: Only for the next response, respond strictly in this JSON format:\n"
                    '{\n  "museums_near_you": [<list of English museum names>],\n'
                    '  "notes": "<any additional notes>"\n}\n'
                    "Do not include anything else before or after this JSON. Do not explain. Just output the JSON only."
                )
                })
              chat2 = self.client.chat.completions.create(
                  model="google/gemini-2.0-pro-exp-02-05:free",
                  messages=self.messages,
              )
              raw_response = chat2.choices[0].message.content
              try:
                # Parse response into dict
              #   print(f"this")
                parsed_json = self.extract_json_from_text(raw_response)
              #   print('parsed_json: '+str(parsed_json))
                event = nearby_museums(**parsed_json)
                reply = json.dumps(event.dict(), indent=2)
              except Exception as e:
                  print(f"[Parse Error]: {e}")
                  reply = raw_response  # fallback: show raw model response
              self.messages.append({"role": "assistant", "content": reply})
              return reply
      except Exception as e:
          print(f"[Fallback Triggered]: {e}")
          return self.direct_model_response()

  def cultural_question(self):
      print(f"inside cultural_question")
      chat4 = self.client.beta.chat.completions.parse(
              model="google/gemini-2.0-pro-exp-02-05:free",
              messages=self.messages,
              response_format = CultureProfile
      )
      reply_message = chat4.choices[0].message
      reply = reply_message.content
      self.messages.append({"role": "assistant", "content": reply})
      return reply
      
  def direct_model_response(self):
      chat5 = self.client.chat.completions.create(
              model="google/gemini-2.0-pro-exp-02-05:free",
              messages=self.messages,
          )
      reply_message = chat5.choices[0].message
      reply = reply_message.content
      self.messages.append({"role": "assistant", "content": reply})
      return reply
      
  def route_request(self,user_input: str) -> RequestType:
      """Router LLM call to determine the type of request"""
      print(f"innnnnnn")
      completion = self.client.beta.chat.completions.parse(
          model="google/gemini-2.0-pro-exp-02-05:free",
          messages=[
              {
                  "role": "system",
                  "content": (
                      "You are a router model. Your task is to classify the user's message into one of three types:\n\n"
                      "1. **tool_call** → The user is asking to use a specific tool or function (e.g., get nearby museums, retrieve model info from database, etc.).\n\n"
                      "2. **cultural_question** → The user is asking for a complete, broad overview of a country’s culture. This means they want detailed cultural insights across many aspects such as history, religion, traditions, values, food, social behavior, festivals, communication style, clothing, etc.\n"
                      "**Important:** If the user asks only about **one specific aspect** (like just food, religion, or clothing), this should NOT be classified as a cultural_question — it should be classified as **direct_model_response** instead.\n\n"
                      "3. **direct_model_response** → Any other type of message that does not require a tool or a full cultural overview. This includes questions about specific cultural elements, greetings, jokes, general conversations, facts, advice, or casual questions.\n\n"
                      "Based on the user input, return the most appropriate request_type, a cleaned description of the user’s intent, and a confidence score between 0 and 1."
                  ),
              },
              {"role": "user", "content": user_input},
          ],
          # tools=self.tools,
          response_format=RequestType,
      )
      result = completion.choices[0].message.parsed
      print(f"[Routing Decision]: {result.request_type} | Confidence: {result.confidence_score}")
      if(result.request_type=="tool_call"):
          reply = self.tool_call(user_input)
      elif(result.request_type=="cultural_question"):
          reply = self.cultural_question()
      else:
          reply = self.direct_model_response()
      return reply

  def generate_response(self, user_message):
      self.messages.append({"role": "user", "content": user_message})
      result = self.route_request(user_message)
      try:
          return result 
      except Exception as e:
          return "error, please try again"

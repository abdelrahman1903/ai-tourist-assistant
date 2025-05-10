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




# class CulturalAttribute(BaseModel):
#     attribute: str = Field(description="Name of the cultural attribute")
#     description: str = Field(description="Explanation of what this attribute means in the country's cultural context")

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
        #     response_format = CultureProfile,
        #     #tools=self.tools,
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


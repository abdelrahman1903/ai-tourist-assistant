import requests
from dotenv import load_dotenv
import google.generativeai as genai
import os
from pydantic import BaseModel, Field
from typing import List
from pydantic.types import StrictBool
import json

load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")
foursquare_key = os.getenv("Foursquare_API_KEY")
if not api_key:
    raise ValueError("Missing OPENROUTER_API_KEY. Did you forget to set it in your .env file?")
genai.configure(api_key=api_key)
LLMmodel = genai.GenerativeModel(
    model_name="gemini-2.5-flash-preview-04-17",
)

class Place(BaseModel):
    place_name: str = Field(description="The name of the place")
    address: str = Field(description="The address of the place, or 'address unavailable' if not available.")
    distance: str = Field(description="Distance in meters.")

class PlacesList(BaseModel):
    places_list: List[Place]
    status: StrictBool = Field(description="True if the value is valid, or false if no sufficient data, or empty palces list.")

class UpdatedGeographicAwarnessTool:
    # Search for places near a given latitude and longitude using Foursquare Places API.
    def search_places(query,lat, lon,language, radius=30000):
        print(query)
        print(language)
        print(lat,lon)
        lat = 29.9877557
        lon = 31.4419752
        API_KEY = foursquare_key  # Replace with your actual key
        url = "https://api.foursquare.com/v3/places/search"

        headers = {
            "Accept": "application/json",
            "Authorization": API_KEY
        }

        params = {
            "ll": f"{lat},{lon}",
            "query": query,
            # "categories": "19027",
            # "categories": "19027,19014,19025,10023,19030,16032,16014",  # Museums, landmarks, galleries, etc.
            "radius": radius,
            "limit": 5,  # You can change this to get more results
            # "locale": "en",  # <-- this line forces results in English
            "sort": "DISTANCE"  # or "DISTANCE"
        }

        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        # print(data)
        results = []
        for place in data.get("results", []):
            results.append({
                "name": place.get("name"),
                "address": place.get("location", {}).get("formatted_address"),
                "distance": place.get("distance")
            })
        print(results)
        messages = [{
            "role": "user",
            "parts": [(
                f"Translate the following list of places: {results} into this language: {language}. "
                "Return a complete JSON object that strictly follows the provided schema. "
                "Include *all* attributes from the schema. Only provide the translated JSON, do not include any explanations, the original data, or additional information."
            )]
        }]
        response = LLMmodel.generate_content(
            contents = messages,
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": PlacesList,
                "temperature": 0,
            }
        )
        reply = response.candidates[0].content.parts[0].text
         # ✅ Validate using your schema
        print(reply)
        try:
            parsed = PlacesList.parse_raw(reply)
            print(parsed)
            return parsed.dict()
        except Exception as e:
            print("[!] Failed to parse PlacesList:", e)
            return {"status": False, "places_list": []}

    # results = search_places(lat=31.2407745, lon=29.9631184, query="hotel")
# messages = [{"role": "user","parts": (
#     [f"Translate the following list of places to English.\n\n{results}. Use the data to return a full JSON object that strictly follows the provided schema."
#     "You must return a full JSON object that strictly follows the schema. Include *all* of the schemas' attributes"]
# )}]
# response = LLMmodel.generate_content(
#     contents = messages,
#     generation_config={
#         "response_mime_type": "application/json",
#         "response_schema": PlacesList,
#         "temperature": 0,
#     }
# )
# reply = response.text
    # print(results)
    # for idx, place in enumerate(results, 1):
    #     print(f"{idx}. {place['name']} - {place['address']} ({place['distance']}m away)")

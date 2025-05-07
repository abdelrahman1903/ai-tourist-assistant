import requests

# Get location from ipinfo.io
try:
    response = requests.get("https://ipinfo.io/json", timeout=10)
    response.raise_for_status()  # Raises an error for bad responses (4xx, 5xx)
    data = response.json()
    
    if "loc" in data:
        lat, lon = data["loc"].split(",")
        lat = "31.2001"
        lon = "29.9187"
    else:
        raise ValueError("Location data not found in response")
    
    print(f"Latitude: {lat}, Longitude: {lon}")

    # Define the Overpass API query
    query = f"""
    [out:json];
    (
      node(around:50000, {lat}, {lon})["tourism"="museum"];
      way(around:50000, {lat}, {lon})["tourism"="museum"];
      relation(around:50000, {lat}, {lon})["tourism"="museum"];
    );
    out body;
    """

    # Send request to Overpass API
    overpass_url = "https://overpass-api.de/api/interpreter"
    overpass_response = requests.get(overpass_url, params={"data": query}, timeout=15)
    overpass_response.raise_for_status()  # Raise an error for bad responses

    # Check if request was successful
    data = overpass_response.json()
    for element in data["elements"]:
        tags = element["tags"]
        
        name_en = tags.get("name:en", "Unknown")
        name_ar = tags.get("name:ar", "N/A")
        museum_type = tags.get("museum", "N/A")
        opening_hours = tags.get("opening_hours", "N/A")
        wikidata = tags.get("wikidata", "")
        wikidata_link = f"https://www.wikidata.org/wiki/{wikidata}" if wikidata else "N/A"

        print(f"- **{name_en}** ({name_ar})")
        print(f"  - Type: {museum_type.capitalize()}")
        print(f"  - Opening Hours: {opening_hours}")
        print(f"  - Wikidata: {wikidata_link}\n")

except requests.exceptions.RequestException as e:
    print("Network error:", e)
except ValueError as ve:
    print("Data error:", ve)
except Exception as ex:
    print("An unexpected error occurred:", ex)

import requests
class GeographicAwarness:
    # Get location from ipinfo.io
    @staticmethod
    def nearLocations():
        try:
            print("in")
            response = requests.get("https://ipinfo.io/json", timeout=10)
            response.raise_for_status()  # Raises an error for bad responses (4xx, 5xx)
            data = response.json()
            
            if "loc" in data:
                lat, lon = data["loc"].split(",")
                lat = "31.2001"
                lon = "29.9187"
                print("lat:"+lat+" "+lon)
            else:
                raise ValueError("Location data not found in response")
            
            print(f"Latitude: {lat}, Longitude: {lon}")

            # Define the Overpass API query
            query = f"""
            [out:json];
            (
            node(around:60000, {lat}, {lon})["tourism"="museum"];
            way(around:60000, {lat}, {lon})["tourism"="museum"];
            relation(around:60000, {lat}, {lon})["tourism"="museum"];
            );
            out body;
            """

            # Send request to Overpass API
            overpass_url = "https://overpass-api.de/api/interpreter"
            overpass_response = requests.get(overpass_url, params={"data": query}, timeout=30)
            overpass_response.raise_for_status()  # Raise an error for bad responses

            # Check if request was successful
            data = overpass_response.json()
            museums = []

            for element in data.get("elements", []):
                tags = element.get("tags", {})
                museum_info = {
                    "name_en": tags.get("name:en", "Unknown"),
                    "name_ar": tags.get("name:ar", "N/A"),
                    "type": tags.get("museum", "N/A"),
                    "opening_hours": tags.get("opening_hours", "N/A"),
                    "wikidata": f"https://www.wikidata.org/wiki/{tags.get('wikidata')}" if tags.get("wikidata") else "N/A"
                }
                museums.append(museum_info)
            print(museums)
            return museums  # Return structured list of museums

        except requests.exceptions.RequestException as e:
            print("Network error:", e)
        except ValueError as ve:
            print("Data error:", ve)
        except Exception as ex:
            print("An unexpected error occurred:", ex)
    # locations = nearLocations()
    # print(locations)
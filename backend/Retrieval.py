import requests
import json

class Retrieval:
    # Get location from ipinfo.io
    @staticmethod
    def search_db(question: str):
        try:
            print("inside data base")
            """
            Load the whole knowledge base from the JSON file.
            (This is a mock function for demonstration purposes, we don't search)
            """
            with open("DB.json", "r") as data:
                return json.load(data)
        except requests.exceptions.RequestException as e:
            print("Network error:", e)
        except ValueError as ve:
            print("Data error:", ve)
        except Exception as ex:
            print("An unexpected error occurred:", ex)

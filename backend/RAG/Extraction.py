from docling.document_converter import DocumentConverter
# from utils.sitemap import get_sitemap_urls
from pydantic import BaseModel, Field
from typing import Literal
from dotenv import load_dotenv
# from openai import OpenAI
import os
from google import genai
# from google.genai import types
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")
converter = DocumentConverter()
if not api_key:
    raise ValueError("Missing OPENROUTER_API_KEY. Did you forget to set it in your .env file?")
        
client =  genai.Client(
    api_key=api_key,  # Use environment variable instead of hardcoded key
)

def extract_json_from_text(document_path):

    # --------------------------------------------------------------
    # Basic PDF extraction
    # --------------------------------------------------------------

    result = converter.convert(document_path)
    document = result.document    
    print("done converting")
    markdown_output = document.export_to_markdown()
    # json_output = document.export_to_dict()
    # print(markdown_output)
    prompt = (
        "You are a helpful assistant. Summarize the following resume into a descriptive summary "
        "that could be stored as metadata for quick retrieval:\n\n"
        f"{markdown_output}"
    )
    response = model.generate_content(messages)
    # messages.append({"role": "user", "content": markdown_output})
    chat5 = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )
    reply = chat5.text
    print(reply)
extract_json_from_text(r"C:\Users\abdel\Downloads\Abdelrahman_Zakzouk_Resume__New.pdf")
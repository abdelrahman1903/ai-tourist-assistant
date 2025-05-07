from dotenv import load_dotenv
from openai import OpenAI
from Summarization import Summarization
from pydantic import BaseModel, Field
import os
import json

load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

class Meta_data(BaseModel):
    FileName: list[str] =  Field(description="the name of the file. extracted from the path")
    FilePath: str = Field(description="the path of the file.")
    FileSummary: str = Field(description="A summary of the file contents")

# def is_valid_json_string(s):
#     try:
#         json.loads(s)
#         return True
#     except (json.JSONDecodeError, TypeError):
#         return False

def insert_to_metaData(record: Meta_data, filename="metadata.json"):
    """Insert a metadata record into a JSON file, handling missing or empty files."""
    data = []
    if os.path.exists(filename):
        with open(filename, "r") as f:
            try:
                content = f.read().strip()
                if content:
                    data = json.loads(content)
            except json.JSONDecodeError:
                print(f"⚠️ Warning: {filename} is not valid JSON. Starting with empty list.")
    
    data.append(record.dict())

    with open(filename, "w") as f:
        json.dump(data, f, indent=4)
    print(f"✅ Metadata for {record.FileName} saved to {filename}")
class MetaData:
    def __init__(self):
        if not api_key:
            raise ValueError("Missing OPENROUTER_API_KEY. Please set it in your .env file.")
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        )
    def metaData_instance(self,document_path):
        summary = Summarization().Summarize(document_path)
        messages = [{"role": "system", "content": "You are a kind, helpful assistant. that should create a meta data record for the inputed file. given it path and summary"}]
        messages.append({"role": "user", "content": f"here is the file path: {document_path} and the summary: {summary}"})
        chat4 = self.client.beta.chat.completions.parse(
            model="google/gemini-2.0-flash-exp:free",
            messages=messages,
            response_format = Meta_data
        )
        # reply_message = chat4.choices[0].message
        # reply = reply_message.content
        reply = chat4.choices[0].message.parsed
        print(f"this should be the metadata record:",reply)
        # print(test,is_valid_json_string(reply))
        insert_to_metaData(reply)

# MetaData().metaData_instance("uploads/Abdelrahman_Zakzouk_Resume.pdf")
      

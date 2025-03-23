from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# from Response_Formate import Response_Formate
from Tool_Calls import Tool_Calls

app = FastAPI()

# response_format__instance = Response_Formate()
Tool_Calls__instance = Tool_Calls()

# Allow frontend to access backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define request body structure
class TextRequest(BaseModel):
    text: str

@app.get("/")
def read_root():
    return {"message": "FastAPI is running!"}

@app.post("/tutorial")  # ✅ Change to POST
async def chat(request: TextRequest):
    user_text = request.text
    # response = response_format__instance.generate_response(user_text)
    response = Tool_Calls__instance.generate_response(user_text)
    return {"response": response}  # ✅ Ensure the correct response field


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

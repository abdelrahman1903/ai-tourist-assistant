from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from model import Model  # Ensure you have a Model class defined in model.py

app = FastAPI()
model_instance = Model()  # Instantiate the model

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

@app.post("/chat")  # ✅ Change to POST
async def chat(request: TextRequest):
    user_text = request.text
    response = model_instance.generate_response(user_text)
    return {"response": response}  # ✅ Ensure the correct response field


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

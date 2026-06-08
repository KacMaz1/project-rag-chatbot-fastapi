from fastapi import FastAPI
from pydantic import BaseModel

from agent_graph import chat_with_agent
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    user_message: str
    thread_id: str = "default"

class ChatResponse(BaseModel):
    response: str

@app.get("/")
def home():
    return {
        "message": "api działa"
    }

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    answer = chat_with_agent(
        user_message=request.user_message,
        thread_id=request.thread_id
    )
    return ChatResponse(response=answer)

from fastapi import FastAPI
from pydantic import BaseModel
from agent.langgraph_agent import run_agent

app = FastAPI()

class Message(BaseModel):
    query: str

@app.post("/ask")
def ask_agent(message: Message):
    response = run_agent(message.query)
    return {"response": response}

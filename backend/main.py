from fastapi import FastAPI
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
from modules.env import settings
from modules.ai import agent

app = FastAPI()


class questions(BaseModel):
    question: str

@app.post("/api/get-questions")
async def get_questions(data: questions):
    ques = data.question
    res = agent.invoke({"messages": [HumanMessage(content=ques)]})
    return res['messages'][1].content


from fastapi import FastAPI
from fastapi.responses import JSONResponse
from modules.env import settings
from modules.ai import invoke_researcher, invoke_conversation
from modules.models import questions, validationRoute, conversationRoute
import uuid

app = FastAPI()



@app.post("/api/get-questions")
async def get_questions(data: questions):
    thread_id = uuid.uuid4()
    name = data.name
    desc = data.desc
    res = invoke_researcher(thread_id=thread_id, name=name, one_liner=desc, resume_val={})
    print(res["__interrupt__"])
    return JSONResponse(status_code=200, content={
        "interrupt": res["__interrupt__"][0].value, 
        "thread_id": str(thread_id)
    })


@app.post("/api/validate")
async def validate(data: validationRoute):
    isValid = data.is_valid
    additional_info = data.additional_info
    thread_id = data.thread_id
    res = invoke_researcher(thread_id=thread_id, resume_val={
        "isValid": isValid, 
        "issues": additional_info
    })

    return res['question_generator']

@app.post("/api/conversation")
async def conversation(data: conversationRoute):
    thread_id = data.thread_id
    message = data.message
    res = invoke_conversation(thread_id=thread_id, message=message)
    return res
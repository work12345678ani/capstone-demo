from fastapi import Depends, FastAPI, HTTPException, Request, Response, status, Form
from fastapi.responses import JSONResponse
from modules.env import settings
from modules.ai import invoke_researcher, invoke_conversation
from modules.res_models import questions, validationRoute, conversationRoute, RegisterIn, LoginIn
import uuid
from typing import Annotated, Optional
from modules.db import get_db
from modules.models import User, Session
from modules.authenticate import (
    RegisterIn,
    LoginIn,
    get_password_hash,
    verify_password,
    create_session,
    delete_session,
    set_session_cookie,
    clear_session_cookie,
    get_current_user,
)
from sqlalchemy.orm import Session as DBSession


app = FastAPI()


@app.post("/api/register", status_code=201)
def register(data: Annotated[RegisterIn, Form()], db: DBSession = Depends(get_db)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    user = User(
        email=data.email,
        username=data.username,
        password_hash=get_password_hash(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "email": user.email, "username": user.username}


@app.post("/api/login")
def login(data: LoginIn, response: Response, db: DBSession = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    sid = create_session(db, user.id)
    set_session_cookie(response, sid)
    return {"ok": True}

@app.post("/api/logout")
def logout(request: Request, response: Response, db: DBSession = Depends(get_db)):
    sid = request.cookies.get("session_id")  # keep in sync with auth.SESSION_COOKIE_NAME if you change it
    if sid:
        delete_session(db, sid)
    clear_session_cookie(response)
    return {"ok": True}

@app.get("/api/me")
def me(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "email": current_user.email, "username": current_user.username}


@app.post("/api/get-questions")
async def get_questions(data: questions, current_user: User = Depends(get_current_user)):
    thread_id = uuid.uuid4()
    name = data.name
    desc = data.desc
    res = invoke_researcher(thread_id=thread_id, name=name, one_liner=desc, resume_val={})
    print(res["__interrupt__"])
    return JSONResponse(status_code=status.HTTP_200_OK, content={
        "interrupt": res["__interrupt__"][0].value, 
        "thread_id": str(thread_id)
    })


@app.post("/api/validate")
async def validate(data: validationRoute, current_user: User = Depends(get_current_user)):
    isValid = data.is_valid
    additional_info = data.additional_info
    thread_id = data.thread_id
    res = invoke_researcher(thread_id=thread_id, resume_val={
        "isValid": isValid, 
        "issues": additional_info
    })

    return JSONResponse(status_code=status.HTTP_200_OK, content={"response": res["question_generator"]})

@app.post("/api/conversation")
async def conversation(data: conversationRoute, current_user: User = Depends(get_current_user)):
    thread_id = data.thread_id
    message = data.message
    res = invoke_conversation(thread_id=thread_id, message=message)
    print(res)
    return JSONResponse(status_code=status.HTTP_200_OK, content={"response": res['messages'][-1].content})
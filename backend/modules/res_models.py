from pydantic import BaseModel, EmailStr, Field
from typing import Annotated, Optional, TypedDict
from operator import add
from langgraph.graph.message import add_messages

# Langgraph Output Formats

class ValidatorOutputFormat(BaseModel):
    name: str
    desc: str

class ResponseState(TypedDict):
    name: str
    one_liner: str
    updated_name: str
    updated_desc: str
    issues: str = ""
    background_info: str
    topic_information: str
    question_generator: str

class ConversationState(TypedDict):
    messages: Annotated[list, add_messages]

# FastAPI Route models

class questions(BaseModel):
    name: str
    desc: str

class validationRoute(BaseModel):
    thread_id: str
    is_valid: bool
    additional_info: str

class conversationRoute(BaseModel):
    thread_id: str
    message: str

class RegisterIn(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=8, max_length=128)

class LoginIn(BaseModel):
    email: EmailStr
    password: str


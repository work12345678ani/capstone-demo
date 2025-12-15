from pydantic import BaseModel
from typing import Annotated, Optional, TypedDict

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


# FastAPI Route models

class questions(BaseModel):
    name: str
    desc: str

class validationRoute(BaseModel):
    thread_id: str
    is_valid: bool
    additional_info: str
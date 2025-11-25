from fastapi import APIRouter
from pydantic import BaseModel
from sql_generator import pipeline_generate_sql

router = APIRouter()

class PromptPayload(BaseModel):
    prompt: str


@router.post("/generate-sql", tags=["Projeto TAES"],)
def generate_sql(payload: PromptPayload):
    return {
        "SQL": pipeline_generate_sql(payload.prompt)
    }

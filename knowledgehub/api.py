from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from knowledgehub.answer import ask_question
from knowledgehub.upload import upload_document

router = APIRouter()


class QuestionRequest(BaseModel):
    question: str


@router.post("/documents", status_code=201)
async def create_document(file: UploadFile = File(...)) -> dict:
    data = await file.read()
    try:
        return upload_document(file.filename or "", data)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/questions")
def create_question(body: QuestionRequest) -> dict:
    try:
        return ask_question(body.question)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

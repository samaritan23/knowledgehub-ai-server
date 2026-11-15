from fastapi import APIRouter, File, HTTPException, UploadFile

from knowledgehub.upload import upload_document

router = APIRouter()


@router.post("/documents", status_code=201)
async def create_document(file: UploadFile = File(...)) -> dict:
    data = await file.read()
    try:
        return upload_document(file.filename or "", data)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

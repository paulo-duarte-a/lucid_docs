from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.concurrency import run_in_threadpool
from fastapi.openapi.models import Example
from typing import Annotated, Any, Dict, Optional
from lucid_docs.core.security import get_current_active_user
from lucid_docs.models.database import User
from lucid_docs.services.file_processing import process_pdf
from lucid_docs.utils.storage import save_temp_file
from lucid_docs.core.config import settings

router = APIRouter(prefix="/upload", tags=["File Upload"])

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

@router.post("/pdf", 
             summary="Upload PDF File", 
             description="Process and store a PDF file.",
             response_model=Dict[str, Any])
async def upload_pdf(
    file: Annotated[
        UploadFile,
        File(
            description="Accepts only PDF files",
            examples=[
                Example(
                    value="arquivo.pdf",
                    summary="PDF Example"
                )
            ],
        ),
    ],
    current_user: Annotated[User, Depends(get_current_active_user)],
    chat_id: Annotated[UUID, Form(description="UUIDv4 identifier for the process")]
):
    """
    Upload and process a PDF file.

    This endpoint receives a PDF file, saves it to temporary storage,
    processes it, and returns processed metadata. It also optionally accepts
    a UUIDv4 that will be validated before processing.
    
    Args:
        file (UploadFile): The PDF file to be uploaded.
        current_user (User): The current active user.
        chat_id (Optional[UUID]): An optional UUIDv4 identifier.

    Returns:
        dict: A confirmation message and metadata if the file was processed successfully,
              or an error message with a 400 status code if validations fail.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Invalid file format. Only PDF files are accepted.")

    if chat_id is not None and chat_id.version != 4:
        raise HTTPException(status_code=400, detail="UUID must be version 4.")

    if file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File size exceeds the maximum limit of {MAX_FILE_SIZE / (1024 * 1024)} MB.")

    temp_path = await run_in_threadpool(save_temp_file, file, settings.TEMP_STORAGE_PATH)
    processed_data = await run_in_threadpool(process_pdf, temp_path, file.filename, current_user.username, str(chat_id))

    return {"message": "File processed successfully", "metadata": processed_data}

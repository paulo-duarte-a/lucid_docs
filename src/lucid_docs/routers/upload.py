from uuid import UUID
from fastapi import APIRouter, Depends, UploadFile, File, Form
from fastapi.openapi.models import Example
from typing import Annotated, Optional
from lucid_docs.core.security import get_current_active_user
from lucid_docs.models.database import User
from lucid_docs.services.file_processing import process_pdf
from lucid_docs.utils.storage import save_temp_file
from lucid_docs.core.config import settings

router = APIRouter(prefix="/upload", tags=["File Upload"])

@router.post("/pdf", summary="Upload PDF File", description="Process and store a PDF file.")
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
    uuid: Annotated[Optional[UUID], Form(description="UUIDv4 identifier for the process")] = None
):
    """
    Upload and process a PDF file.

    This endpoint receives a PDF file, saves it to temporary storage,
    processes it, and returns processed metadata. It also optionally accepts
    a UUIDv4 that will be validated before processing.
    
    Args:
        file (UploadFile): The PDF file to be uploaded.
        current_user (User): The current active user.
        uuid (Optional[UUID]): An optional UUIDv4 identifier.

    Returns:
        dict: A confirmation message and metadata if the file was processed successfully,
              or an error message with a 400 status code if validations fail.
    """
    if file.content_type != "application/pdf":
        return {"error": "Invalid file format. Only PDF files are accepted."}, 400

    if uuid is not None and uuid.version != 4:
        return {"error": "UUID must be version 4."}, 400

    temp_path = await save_temp_file(file, settings.TEMP_STORAGE_PATH)
    processed_data = process_pdf(temp_path, file.filename, current_user.username)

    return {"message": "File processed successfully", "metadata": processed_data}

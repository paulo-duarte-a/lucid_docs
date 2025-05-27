from fastapi import APIRouter, Depends, UploadFile
from lucid_docs.core.security import get_current_active_user
from lucid_docs.services.file_processing import process_pdf
from lucid_docs.utils.storage import save_temp_file
from lucid_docs.core.config import settings

router = APIRouter(prefix="/upload", tags=["File Upload"])

@router.post("/pdf", dependencies=[Depends(get_current_active_user)])
async def upload_pdf(file: UploadFile):
    temp_path = await save_temp_file(file, settings.TEMP_STORAGE_PATH)
    processed_data = await process_pdf(temp_path)
    return {"message": "File processed successfully", "metadata": processed_data}

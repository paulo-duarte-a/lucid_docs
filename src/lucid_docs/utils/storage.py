from pathlib import Path
import shutil
import uuid

from fastapi import UploadFile

async def save_temp_file(file: UploadFile, temp_dir: str) -> Path:
    file_path = Path(temp_dir) / f"{uuid.uuid4()}.pdf"
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return file_path
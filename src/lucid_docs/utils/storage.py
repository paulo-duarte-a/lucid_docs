from pathlib import Path
import shutil
import uuid

from fastapi import UploadFile

def save_temp_file(file: UploadFile, temp_dir: str) -> Path:
    """
    Save an uploaded file to a temporary directory.

    This function takes an UploadFile object and a specified temporary directory path,
    generates a unique filename with a .pdf extension using UUID, and writes the file's
    content to the generated path. It returns the Path object of the saved file.

    Parameters:
        file (UploadFile): The uploaded file to be saved.
        temp_dir (str): The directory where the file will be temporarily stored.

    Returns:
        Path: The path to the saved temporary file.
    """
    file_path = Path(temp_dir) / f"{uuid.uuid4()}.pdf"
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return file_path
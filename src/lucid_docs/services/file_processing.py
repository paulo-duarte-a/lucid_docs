from datetime import datetime
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from lucid_docs.dependencies import chroma

def process_pdf(file_path: Path, filename: str, username: str, chat_id: str = None):
    """
    Process a PDF file by extracting pages, splitting the text into chunks,
    attaching metadata, and storing the documents.

    Parameters:
        file_path (Path): The path to the PDF file.
        filename (str): The original file name as provided by the user.
        username (str): The identifier for the user.
        chat_id (str, optional): An optional chat identifier.

    Returns:
        dict: A dictionary with the processing status, the number of pages,
              and the number of chunks created.
    """
    loader = PyPDFLoader(str(file_path))
    pages = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    splits = text_splitter.split_documents(pages)

    for split in splits:
        metadata = {
            "user_id": username,
            "hash_file_name": file_path.name,
            "file_name": filename,
            "timestamp": datetime.now().isoformat()
        }
        if chat_id:
            metadata["chat_id"] = chat_id

        split.metadata.update(metadata)

    chroma.add_documents(documents=splits)

    return {
        "status": "processed",
        "page_count": len(pages),
        "chunks": len(splits)
    }
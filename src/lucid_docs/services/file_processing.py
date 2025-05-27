from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from lucid_docs.core.config import settings
from lucid_docs.dependencies import embeddings


async def process_pdf(file_path: Path):
    loader = PyPDFLoader(str(file_path))
    pages = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    splits = text_splitter.split_documents(pages)

    Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory=settings.CHROMA_PERSIST_DIR,
        collection_name=settings.CHROMA_COLLECTION_NAME
    )

    return {
        "status": "processed",
        "page_count": len(pages),
        "chunks": len(splits)
    }
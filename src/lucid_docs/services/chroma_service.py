import logging
from lucid_docs.core.config import settings
from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import PromptTemplate
from lucid_docs.dependencies import embeddings, llm



logger = logging.getLogger(__name__)

def get_chroma_client():
    return Chroma(
        persist_directory=settings.CHROMA_PERSIST_DIR,
        collection_name=settings.CHROMA_COLLECTION_NAME,
        embedding_function=embeddings
    )

async def query_collection(question: str, top_k: int = 3):
    retriever = get_chroma_client().as_retriever(search_kwargs={"k": top_k})

    prompt_template = """
    Responda à pergunta com base apenas no contexto abaixo:
    Contexto: {context}
    
    Pergunta: {question}
    Resposta:
    """
    
    custom_rag_prompt = PromptTemplate.from_template(prompt_template)

    rag_chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | custom_rag_prompt
        | llm
        | StrOutputParser()
    )

    return await rag_chain.ainvoke(question)
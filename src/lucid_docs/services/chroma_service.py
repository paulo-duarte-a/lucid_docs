import logging
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import PromptTemplate
from lucid_docs.dependencies import get_llm, get_chroma

logger = logging.getLogger(__name__)

async def query_collection(question: str, username: str, chat_id: str = None, top_k: int = 3):
    """
    Query the collection using a Retrieval-Augmented Generation (RAG) chain.

    This function retrieves up to `top_k` documents from the Chroma store that belong
    to the specified user, builds a prompt with the retrieved context and the given question,
    and then invokes a language model chain to generate an answer based solely on the provided context.

    Args:
        question (str): The question to be answered.
        username (str): The user identifier used to filter the documents.
        chat_id (str): The identifier for the chat session.
        top_k (int, optional): The number of documents to retrieve. Defaults to 3.

    Returns:
        str: The answer generated by the language model.
    """
    if chat_id:
        filter_query = {"$and": [{"user_id": username}, {"chat_id": chat_id}]}
    else:
        filter_query = {"user_id": username}

    logger.debug(f"Filter query for Chroma: {filter_query}")

    retriever = get_chroma().as_retriever(
        search_kwargs={
            "k": top_k,
            "filter": filter_query
        }
    )

    prompt_template = """
    Responda à pergunta com base apenas no contexto fornecido abaixo:
    Contexto: {context}
    
    Pergunta: {question}
    Resposta:
    """
    
    custom_rag_prompt = PromptTemplate.from_template(prompt_template)

    rag_chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | custom_rag_prompt
        | get_llm()
        | StrOutputParser()
    )

    try:
        response = await rag_chain.ainvoke(question)
    except Exception as e:
        logger.error(f"Error during RAG chain invocation: {e}")
        response = "An error occurred while processing your request. Please try again later."

    return response

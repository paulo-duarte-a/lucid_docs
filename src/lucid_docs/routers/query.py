import logging
from datetime import datetime
import pytz
from uuid import UUID
from typing import Annotated
from fastapi import APIRouter, Depends
from lucid_docs.core.security import get_current_active_user
from lucid_docs.services.chroma_service import query_collection
from lucid_docs.models.schemas import QueryRequest, QueryResponse
from lucid_docs.models.database import User, Conversation, Message
from lucid_docs.dependencies import messages_collection

router = APIRouter(prefix="/chat", tags=["Chat"])

logger = logging.getLogger(__name__)

def get_api_docstring():
    """
    Router for handling chat related queries.

    This module provides endpoints for processing chat related queries.
    """

@router.post("/", response_model=QueryResponse)
async def ask_question(
    request: QueryRequest, 
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Process a chat query request and return the corresponding results.

    This endpoint receives a query through the request body, performs the query operation
    using the provided user's credentials, and returns the query results.

    Args:
        request (QueryRequest): The request body containing the chat question and additional parameters.
        current_user (User): The active user obtained from the security dependency.

    Returns:
        QueryResponse: A response model containing the results from the query.
    """
    user_message = Message(
        chat_id=request.chat_id,
        username=current_user.username,
        role='user',
        content=request.question,
        timestamp=datetime.now(pytz.utc).isoformat()
    )

    messages_collection.insert_one(
        user_message.model_dump(by_alias=True, exclude=["id"])
    )

    results = await query_collection(request.question, current_user.username, request.top_k)
    
    assistant_message = Message(
        chat_id=request.chat_id,
        username=current_user.username,
        role='assistant',
        content=results,
        timestamp=datetime.now(pytz.utc).isoformat()
    )

    messages_collection.insert_one(
        assistant_message.model_dump(by_alias=True, exclude=["id"])
    )
   
    return {"results": results}


@router.get(
    "/conversation/{id}",
    response_description="List all messages in the conversation",
    response_model=Conversation,
    response_model_by_alias=False,
)
async def list_messages(id: str, current_user: Annotated[User, Depends(get_current_active_user)],):
    """
    Retrieve all messages in a conversation by its ID.
    This endpoint fetches all messages associated with a specific conversation ID
    and returns them in a structured format.
    Args:
        id (str): The unique identifier of the conversation.
    Returns:
        Conversation: A structured response containing all messages in the conversation.
    """
    if not id:
        raise ValueError("Conversation ID must be provided")
    if not UUID(id).version == 4:
        raise ValueError("Conversation ID must be a valid UUID version 4")

    logger.info(f"Fetching messages for conversation ID: {id} by user: {current_user.username}")

    conversation_messages = await messages_collection.find({
        "chat_id": id, "username": current_user.username
    }).to_list(length=None)

    return Conversation(messages=conversation_messages)
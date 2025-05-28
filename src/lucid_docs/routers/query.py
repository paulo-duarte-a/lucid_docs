import logging
from uuid import UUID
from pymongo import ASCENDING
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException
from lucid_docs.core.security import get_current_active_user
from lucid_docs.services.chroma_service import query_collection
from lucid_docs.models.schemas import QueryRequest, QueryResponse, RoleEnum
from lucid_docs.models.database import User, Conversation, Message
from lucid_docs.dependencies import messages_collection
from lucid_docs.utils.date import current_utc_timestamp

router = APIRouter(prefix="/chat", tags=["Chat"])

logger = logging.getLogger(__name__)


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
        role=RoleEnum.user,
        content=request.question,
        timestamp=current_utc_timestamp()
    )

    messages_collection.insert_one(
        user_message.model_dump(by_alias=True, exclude=["id"])
    )

    results = await query_collection(request.question, current_user.username, request.top_k)
    
    assistant_message = Message(
        chat_id=request.chat_id,
        username=current_user.username,
        role=RoleEnum.assistant,
        content=results,
        timestamp=current_utc_timestamp()
    )

    messages_collection.insert_one(
        assistant_message.model_dump(by_alias=True, exclude=["id"])
    )
   
    return {"results": results}


@router.get(
    "/conversation",
    response_description="List all messages of the user",
    response_model=Conversation,
    response_model_by_alias=False,
)
@router.get(
    "/conversation/{id}",
    response_description="List messages by conversation ID",
    response_model=Conversation,
    response_model_by_alias=False,
)
async def list_messages(
    current_user: Annotated[User, Depends(get_current_active_user)],
    id: Optional[str] = None
):
    """
    Retrieve messages by conversation ID if provided, or all user messages.

    Args:
        id (Optional[str]): UUIDv4 of the conversation.
        current_user (User): Authenticated user.

    Returns:
        Conversation: Messages from one or all conversations.
    """
    query = {"username": current_user.username}

    if id:
        try:
            uuid_obj = UUID(id)
            if uuid_obj.version != 4:
                raise HTTPException(status_code=400, detail="Conversation ID must be a valid UUID version 4")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid UUID format")

        query["chat_id"] = id
        logger.info(f"Fetching messages for conversation ID: {id} by user: {current_user.username}")
        conversation_messages = await messages_collection.find(query).to_list(length=None)
    else:
        logger.info(f"Fetching all messages for user: {current_user.username}")
        pipeline = [
            {"$match": {"username": current_user.username}},
            {"$sort": {"timestamp": ASCENDING}},
            {"$group": {
                "_id": "$chat_id",
                "chat_id": {"$first": "$chat_id"},
                "username": {"$first": "$username"},
                "role": {"$first": "$role"},
                "timestamp": {"$first": "$timestamp"},
                "first_message": {"$first": "$content"},
            }},
            {"$project": {
                "chat_id": 1,
                "username": 1,
                "role": 1,
                "timestamp": 1,
                "content": {"$substrCP": ["$first_message", 0, 30]}
            }}
        ]
        conversation_messages = await messages_collection.aggregate(pipeline).to_list(length=None)

    return Conversation(messages=conversation_messages)

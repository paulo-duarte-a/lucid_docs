import logging
from fastapi import APIRouter, Depends
from lucid_docs.core.security import get_current_active_user
from lucid_docs.services.chroma_service import query_collection
from lucid_docs.models.schemas import QueryRequest, QueryResponse

router = APIRouter(prefix="/chat", tags=["Chat"])

logger = logging.getLogger(__name__)

@router.post("/", response_model=QueryResponse, dependencies=[Depends(get_current_active_user)])
async def ask_question(request: QueryRequest):
    results = await query_collection(request.question, request.top_k)
    return {"results": results}

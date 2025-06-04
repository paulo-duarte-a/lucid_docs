import pytest
from uuid import uuid1, uuid4, UUID
from pydantic import ValidationError
import logging

from lucid_docs.models.schemas import (
    RoleEnum,
    QueryRequest,
    QueryResponse,
    Token,
    TokenData
)

logger = logging.getLogger(__name__)


class TestRoleEnum:
    def test_role_enum_values(self):
        assert RoleEnum.user == "user"
        assert RoleEnum.user.value == "user"
        assert RoleEnum.assistant == "assistant"
        assert RoleEnum.assistant.value == "assistant"


class TestQueryRequest:
    def test_query_request_valid_data_defaults(self):
        chat_id_v4 = str(uuid4())
        data = {
            "question": "What is the meaning of life?",
            "chat_id": chat_id_v4
        }
        model = QueryRequest(**data)
        assert model.question == "What is the meaning of life?"
        assert model.chat_id == chat_id_v4
        assert model.top_k == 3  # Default value

    def test_query_request_valid_data_explicit_top_k(self):
        chat_id_v4 = str(uuid4())
        data = {
            "question": "Another question?",
            "chat_id": chat_id_v4,
            "top_k": 5
        }
        model = QueryRequest(**data)
        assert model.question == "Another question?"
        assert model.chat_id == chat_id_v4
        assert model.top_k == 5

    def test_query_request_top_k_constraints(self):
        chat_id_v4 = str(uuid4())
        
        # Valid top_k
        QueryRequest(question="q", chat_id=chat_id_v4, top_k=1)
        QueryRequest(question="q", chat_id=chat_id_v4, top_k=10)

        # top_k less than 1
        with pytest.raises(ValidationError) as excinfo_lt:
            QueryRequest(question="q", chat_id=chat_id_v4, top_k=0)
        assert "Input should be greater than or equal to 1" in str(excinfo_lt.value)

        # top_k greater than 10
        with pytest.raises(ValidationError) as excinfo_gt:
            QueryRequest(question="q", chat_id=chat_id_v4, top_k=11)
        assert "Input should be less than or equal to 10" in str(excinfo_gt.value)

    def test_query_request_chat_id_validation(self):
        question_str = "Is this a valid chat ID?"
        
        # Valid UUIDv4
        valid_chat_id = str(uuid4())
        model = QueryRequest(question=question_str, chat_id=valid_chat_id)
        assert model.chat_id == valid_chat_id

        # Invalid UUID string
        with pytest.raises(ValidationError) as excinfo_invalid_uuid:
            QueryRequest(question=question_str, chat_id="not-a-uuid")
        # Pydantic's UUID type validation might catch this first, or the custom validator
        assert "UUID" in str(excinfo_invalid_uuid.value) # General check

        # UUIDv1 (should fail custom validator)
        uuid_v1 = str(uuid1())
        with pytest.raises(ValidationError) as excinfo_uuid_v1:
            QueryRequest(question=question_str, chat_id=uuid_v1)
        assert "str must be UUID version 4" in str(excinfo_uuid_v1.value)
        
        # Empty string (should fail UUID conversion)
        with pytest.raises(ValidationError) as excinfo_empty_str:
            QueryRequest(question=question_str, chat_id="")
        assert "UUID" in str(excinfo_empty_str.value) # General check for UUID failure

    def test_query_request_missing_fields(self):
        chat_id_v4 = str(uuid4())
        
        # question missing
        with pytest.raises(ValidationError) as excinfo_q:
            QueryRequest(chat_id=chat_id_v4)
        assert "Field required" in str(excinfo_q.value)
        assert "question" in str(excinfo_q.value) # Check for field name without quotes

        # chat_id missing
        with pytest.raises(ValidationError) as excinfo_cid:
            QueryRequest(question="A question without chat_id")
        assert "Field required" in str(excinfo_cid.value)
        assert "chat_id" in str(excinfo_cid.value) # Check for field name without quotes


class TestQueryResponse:
    def test_query_response_valid_data(self):
        data = {"results": "These are the results."}
        model = QueryResponse(**data)
        assert model.results == "These are the results."

    def test_query_response_missing_results(self):
        with pytest.raises(ValidationError) as excinfo:
            QueryResponse() # results is required
        assert "Field required" in str(excinfo.value)
        assert "results" in str(excinfo.value) # Check for field name without quotes


class TestToken:
    def test_token_valid_data(self):
        data = {"access_token": "abc123xyz", "token_type": "bearer"}
        model = Token(**data)
        assert model.access_token == "abc123xyz"
        assert model.token_type == "bearer"

    def test_token_missing_fields(self):
        with pytest.raises(ValidationError) as excinfo_at:
            Token(token_type="bearer")
        assert "Field required" in str(excinfo_at.value)
        # Corrected assertion: check for the field name without single quotes
        assert "access_token" in str(excinfo_at.value)

        with pytest.raises(ValidationError) as excinfo_tt:
            Token(access_token="abc")
        assert "Field required" in str(excinfo_tt.value)
        # Corrected assertion: check for the field name without single quotes
        assert "token_type" in str(excinfo_tt.value)


class TestTokenData:
    def test_token_data_with_username(self):
        data = {"username": "testuser"}
        model = TokenData(**data)
        assert model.username == "testuser"

    def test_token_data_with_none_username(self):
        data = {"username": None}
        model = TokenData(**data)
        assert model.username is None

    def test_token_data_default_username(self):
        model = TokenData() # username is Optional and defaults to None
        assert model.username is None
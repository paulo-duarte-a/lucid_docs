import pytest
from uuid import uuid4, uuid1
from pydantic import ValidationError, EmailStr

from lucid_docs.models.database import (
    User,
    UserInDB,
    Message,
    Conversation
)

# Helper for generating valid ObjectId-like strings for testing PyObjectId
def get_mock_object_id_str():
    return "60d5ecf0e3b3f3b3f8b3f8b3"

class TestUser:
    def test_user_valid_data_minimal(self):
        data = {"username": "testuser"}
        model = User(**data)
        assert model.username == "testuser"
        assert model.id is None
        assert model.email is None
        assert model.full_name is None
        assert model.disabled is False

    def test_user_valid_data_all_fields(self):
        user_id_str = get_mock_object_id_str()
        # Use the alias "_id" for input
        data = {
            "_id": user_id_str, # Use alias for input
            "username": "anotheruser",
            "email": "test@example.com",
            "full_name": "Test User Full",
            "disabled": True,
        }
        model = User(**data)
        assert model.id == user_id_str
        assert model.username == "anotheruser"
        assert model.email == "test@example.com"
        assert model.full_name == "Test User Full"
        assert model.disabled is True

    def test_user_id_alias(self):
        user_id_str = get_mock_object_id_str()
        
        # Test creating with '_id' (alias) correctly populates the 'id' attribute
        model = User(username="aliastest", _id=user_id_str)
        assert model.id == user_id_str
        
        # Test model_dump by_alias=True uses the alias '_id'
        dumped_data_with_alias = model.model_dump(by_alias=True)
        assert dumped_data_with_alias["_id"] == user_id_str
        assert "id" not in dumped_data_with_alias

        # Test model_dump by_alias=False (or default) uses the field name 'id'
        dumped_data_no_alias = model.model_dump(by_alias=False)
        assert dumped_data_no_alias["id"] == user_id_str
        assert "_id" not in dumped_data_no_alias
        
        # Explicitly test that initializing with 'id=' when alias and default exist
        # results in 'id' being None (reflecting current observed behavior)
        model_init_with_id_name = User(username="aliastest_id_field", id=user_id_str)
        assert model_init_with_id_name.id is None


    def test_user_username_validation(self):
        User(username="valid_user123")
        User(username="VAL")

        with pytest.raises(ValidationError) as excinfo:
            User(username="us")
        assert "String should have at least 3 characters" in str(excinfo.value)

        with pytest.raises(ValidationError) as excinfo:
            User(username="a" * 31)
        assert "String should have at most 30 characters" in str(excinfo.value)

        with pytest.raises(ValidationError) as excinfo:
            User(username="invalid-user!")
        assert "String should match pattern" in str(excinfo.value)
        
    def test_user_email_validation(self):
        User(username="emailtest", email="test@example.com")
        User(username="emailtest", email=None)

        with pytest.raises(ValidationError) as excinfo:
            User(username="emailtest", email="notanemail")
        assert "value is not a valid email address" in str(excinfo.value)


class TestUserInDB:
    valid_user_data = {
        "username": "dbuser",
        "email": "db@example.com",
        "full_name": "DB User",
        "disabled": False,
    }

    def test_userindb_valid_data(self):
        model = UserInDB(**self.valid_user_data, password="ValidPassword1!")
        assert model.username == "dbuser"
        assert model.password == "ValidPassword1!"

    def test_userindb_password_valid(self):
        UserInDB(**self.valid_user_data, password="Password123!")
        UserInDB(**self.valid_user_data, password="S3cureP@ssw0rd")

    def test_userindb_password_invalid_too_short(self):
        with pytest.raises(ValidationError) as excinfo:
            UserInDB(**self.valid_user_data, password="Pass1!")
        assert "String should have at least 8 characters" in str(excinfo.value)

    def test_userindb_password_invalid_no_uppercase(self):
        with pytest.raises(ValidationError) as excinfo:
            UserInDB(**self.valid_user_data, password="password1!")
        assert "Password must include at least one uppercase letter" in str(excinfo.value)

    def test_userindb_password_invalid_no_lowercase(self):
        with pytest.raises(ValidationError) as excinfo:
            UserInDB(**self.valid_user_data, password="PASSWORD1!")
        assert "Password must include at least one lowercase letter" in str(excinfo.value)

    def test_userindb_password_invalid_no_digit(self):
        with pytest.raises(ValidationError) as excinfo:
            UserInDB(**self.valid_user_data, password="Password!")
        assert "Password must include at least one digit" in str(excinfo.value)

    def test_userindb_password_invalid_no_special_char(self):
        with pytest.raises(ValidationError) as excinfo:
            UserInDB(**self.valid_user_data, password="Password123")
        assert "Password must include at least one special character" in str(excinfo.value)

    def test_userindb_password_max_length(self):
        base_valid_pass = "ValidPass1!"
        padding_len = 128 - len(base_valid_pass)
        valid_password_128_chars = base_valid_pass + ("a" * padding_len)
        assert len(valid_password_128_chars) == 128

        UserInDB(**self.valid_user_data, password=valid_password_128_chars)
        
        with pytest.raises(ValidationError) as excinfo:
            UserInDB(**self.valid_user_data, password=valid_password_128_chars + "a")
        assert "String should have at most 128 characters" in str(excinfo.value)


class TestMessage:
    valid_chat_id_str = str(uuid4())
    valid_username = "messageuser"
    
    base_message_data = {
        "chat_id": valid_chat_id_str,
        "username": valid_username,
        "role": "user",
        "content": "Hello there!",
        "timestamp": "2024-01-01T12:00:00Z"
    }

    def test_message_valid_data(self):
        msg_id_str = get_mock_object_id_str()
        data = {**self.base_message_data, "_id": msg_id_str} # Use alias for input
        model = Message(**data)
        assert model.id == msg_id_str
        assert model.chat_id == self.valid_chat_id_str

    def test_message_id_alias(self):
        msg_id_str = get_mock_object_id_str()
        
        # Test creating with '_id' (alias) correctly populates the 'id' attribute
        model = Message(**{**self.base_message_data, "_id": msg_id_str})
        assert model.id == msg_id_str
        
        # Test model_dump by_alias=True uses the alias '_id'
        dumped_data_with_alias = model.model_dump(by_alias=True)
        assert dumped_data_with_alias["_id"] == msg_id_str
        assert "id" not in dumped_data_with_alias

        # Test model_dump by_alias=False (or default) uses the field name 'id'
        dumped_data_no_alias = model.model_dump(by_alias=False)
        assert dumped_data_no_alias["id"] == msg_id_str
        assert "_id" not in dumped_data_no_alias

        # Explicitly test that initializing with 'id=' when alias and default exist
        # results in 'id' being None (reflecting current observed behavior)
        model_init_with_id_name = Message(**{**self.base_message_data, "id": msg_id_str})
        assert model_init_with_id_name.id is None


    def test_message_chat_id_validation(self):
        Message(**self.base_message_data)

        with pytest.raises(ValidationError) as excinfo:
            Message(**{**self.base_message_data, "chat_id": "not-a-uuid"})
        assert "UUID" in str(excinfo.value)

        uuid_v1 = str(uuid1())
        with pytest.raises(ValidationError) as excinfo:
            Message(**{**self.base_message_data, "chat_id": uuid_v1})
        assert "str must be UUID version 4" in str(excinfo.value)

    def test_message_username_validation(self):
        Message(**self.base_message_data)

        with pytest.raises(ValidationError) as excinfo:
            Message(**{**self.base_message_data, "username": "u"})
        assert "String should have at least 3 characters" in str(excinfo.value)
        
        with pytest.raises(ValidationError) as excinfo:
            Message(**{**self.base_message_data, "username": "u@s"})
        assert "String should match pattern" in str(excinfo.value)


    def test_message_required_fields(self):
        required = ["chat_id", "username", "role", "content", "timestamp"]
        for field in required:
            data_copy = self.base_message_data.copy()
            del data_copy[field]
            with pytest.raises(ValidationError) as excinfo:
                Message(**data_copy)
            assert "Field required" in str(excinfo.value)
            assert field in str(excinfo.value)


class TestConversation:
    def test_conversation_valid_data_with_messages(self):
        chat_id = str(uuid4())
        msg_data1 = {
            "_id": get_mock_object_id_str(), "chat_id": chat_id, "username": "user1", "role": "user", 
            "content": "Msg1", "timestamp": "2024-01-01T10:00:00Z"
        }
        msg_data2 = {
            "chat_id": chat_id, "username": "user1", "role": "assistant", 
            "content": "Msg2", "timestamp": "2024-01-01T10:01:00Z"
        }
        conversation = Conversation(messages=[msg_data1, msg_data2])
        assert len(conversation.messages) == 2
        assert isinstance(conversation.messages[0], Message)
        assert conversation.messages[0].content == "Msg1"
        assert conversation.messages[0].id is not None
        assert isinstance(conversation.messages[1], Message)
        assert conversation.messages[1].content == "Msg2"

    def test_conversation_valid_data_empty_messages(self):
        conversation = Conversation(messages=[])
        assert len(conversation.messages) == 0

    def test_conversation_invalid_message_in_list(self):
        chat_id = str(uuid4())
        valid_msg_data = {
            "_id": get_mock_object_id_str(), "chat_id": chat_id, "username": "user1", "role": "user", 
            "content": "Valid", "timestamp": "2024-01-01T10:00:00Z"
        }
        invalid_msg_data = {"username": "user1"}
        
        with pytest.raises(ValidationError) as excinfo:
            Conversation(messages=[valid_msg_data, invalid_msg_data])
        assert "messages.1.chat_id" in str(excinfo.value) 
        assert "Field required" in str(excinfo.value)

    def test_conversation_messages_not_a_list(self):
        with pytest.raises(ValidationError) as excinfo:
            Conversation(messages="not a list")
        assert "Input should be a valid list" in str(excinfo.value)
from unittest.mock import Mock, patch, mock_open
from rasa_sdk import Tracker
import pytest
from bot.ej.conversation import Conversation
from bot.ej.profile import Profile


@pytest.fixture
def conversation_statistics():
    return {
        "votes": 0,
        "missing_votes": 10,
        "participation_ratio": 0.0,
        "total_comments": 20,
        "comments": 0,
        "send_profile_questions": True,
        "votes_to_send_profile_questions": 1,
    }


@pytest.fixture
def dispatcher():
    dispatcher = Mock()
    dispatcher.utter_message = lambda **kwargs: "some_utter"
    return dispatcher


@pytest.fixture
def empty_tracker():
    slots = {
        "has_completed_registration": None,
        "participants_can_add_comments": None,
        "anonymous_votes_limit": None,
        "access_token": None,
        "refresh_token": None,
        "conversation_id": None,
        "conversation_title": None,
        "next_count_to_send_profile_question": 0,
        "send_profile_questions": None,
        "votes_to_send_profile_questions": None,
    }

    def set_slot(slot, value):
        slots[slot] = value

    def get_slot(slot):
        return slots[slot]

    tracker = Mock()
    tracker.sender_id = None
    tracker.conversation_statistics = None
    tracker.get_slot = lambda x: None
    tracker.get_latest_input_channel = lambda: None
    tracker.latest_message = {
        "metadata": {
            "token": "",
            "bot": False,
            "channel_id": "PtSjgJqB29fcy9vFd",
            "channel_name": "mr_davidCarlos-telegram",
            "message_id": "f3yTeCyHAuPNDdQZv",
            "timestamp": "2022-06-20T15:23:17.242Z",
            "user_id": "9H7jF3P6PnStr496r",
            "user_name": "mr_davidCarlos",
            "text": "start 74",
            "siteUrl": "http://localhost:3000",
        }
    }
    tracker.get_slot = get_slot
    tracker.set_slot = set_slot
    return tracker


@pytest.fixture
def tracker():
    slots = {
        "has_completed_registration": False,
        "participant_can_add_comments": False,
        "anonymous_votes_limit": 10,
        "access_token": "1234",
        "refresh_token": "5678",
        "conversation_id": "1",
        "conversation_id_cache": "1",
        "conversation_title": "conversation title",
        "send_profile_questions": True,
        "votes_to_send_profile_questions": 1,
    }

    def set_slot(slot, value):
        slots[slot] = value

    def get_slot(slot):
        return slots[slot]

    tracker = Mock()
    tracker.sender_id = "1234"
    tracker.conversation_statistics = "1234"
    tracker.get_slot = lambda x: "1234"
    tracker.get_latest_input_channel = lambda: "whatsapp"
    tracker.latest_message = {
        "metadata": {
            "token": "",
            "bot": False,
            "channel_id": "PtSjgJqB29fcy9vFd",
            "channel_name": "mr_davidCarlos-telegram",
            "message_id": "f3yTeCyHAuPNDdQZv",
            "timestamp": "2022-06-20T15:23:17.242Z",
            "user_id": "9H7jF3P6PnStr496r",
            "user_name": "mr_davidCarlos",
            "text": "start 74",
            "siteUrl": "http://localhost:3000",
        }
    }
    tracker.get_slot = get_slot
    tracker.set_slot = set_slot
    return tracker


@pytest.fixture
def telegram_tracker(tracker):
    tracker.latest_message = {
        "metadata": {
            "token": "",
            "bot": False,
            "channel_id": "PtSjgJqB29fcy9vFd",
            "channel_name": "mr_davidCarlos-telegram",
            "message_id": "f3yTeCyHAuPNDdQZv",
            "timestamp": "2022-06-20T15:23:17.242Z",
            "user_id": "9H7jF3P6PnStr496r",
            "contact_name": "David Carlos",
            "text": "start 74",
            "siteUrl": "http://localhost:3000",
        }
    }
    return tracker


@pytest.fixture
def anonymous_tracker(tracker):
    tracker.latest_message = {"metadata": {}}
    return tracker


@pytest.fixture
def wpp_tracker(tracker):
    tracker.latest_message = {
        "metadata": {
            "token": "",
            "bot": False,
            "channel_id": "PtSjgJqB29fcy9vFd",
            "channel_name": "mr_davidCarlos-telegram",
            "message_id": "f3yTeCyHAuPNDdQZv",
            "timestamp": "2022-06-20T15:23:17.242Z",
            "user_id": "9H7jF3P6PnStr496r",
            "contact_name": "David Carlos",
            "text": "start 74",
            "siteUrl": "http://localhost:3000",
        }
    }
    return tracker


@pytest.fixture
def comment():
    return {"content": "new comment", "id": "1"}


@pytest.fixture
def extra_data():
    return {
        "id": "123",
        "text": "Test Title",
        "participants_can_add_comments": True,
        "anonymous_votes_limit": 5,
    }


@pytest.fixture
def conversation(tracker, comment, extra_data):
    conversation = Conversation(tracker, extra_data)
    conversation.get_next_comment = Mock()
    conversation.get_next_comment = lambda: comment
    return conversation


@pytest.fixture
def metadata():
    return {"other_keys": " notlivechat"}


@pytest.fixture
def livechat_metadata():
    return {"agent": "livechat"}


@pytest.fixture
def mock_ej_api_response():
    return {
        "user": 1,
        "phone_number": "123456789",
        "ethnicity_choices": 0,
        "gender": 0,
        "age_range": 0,
        "region": 0,
    }


mock_json_content = """
{
    "questions": [
        {
            "id": 1,
            "body": "Qual é o seu gênero?",
            "change": "Gender",
            "put_payload": "gender",
            "answers": [
                {"payload": 1, "title": "Masculino", "description": ""},
                {"payload": 2, "title": "Feminino", "description": ""},
                {"payload": 3, "title": "Outro", "description": ""}
            ]
        }
    ],
    "random_questions": false
}
"""


@pytest.fixture
def mock_profile(mock_ej_api_response, tracker):
    with patch("bot.ej.profile.EjApi.request") as mock_request, patch(
        "bot.ej.profile.Profile.send_answer"
    ) as mock_send_answer, patch(
        "bot.ej.ej_api.EjApi._refresh_access_token"
    ) as mock_refresh_token, patch(
        "builtins.open", mock_open(read_data=mock_json_content)
    ):

        mock_request.return_value.json.return_value = mock_ej_api_response
        mock_request.return_value.status_code = 200
        mock_send_answer.return_value = Mock(status_code=200)
        mock_refresh_token.return_value = None

        mock_profile = Profile(tracker)
        mock_profile.ej_api.access_token = "mock_access_token"
        return mock_profile

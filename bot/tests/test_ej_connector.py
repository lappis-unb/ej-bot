from unittest.mock import Mock, patch

from bot.actions.ej_connector.comment import Comment
from bot.actions.ej_connector.constants import *
from bot.actions.ej_connector.conversation import Conversation
from bot.actions.ej_connector.routes import *
from bot.actions.ej_connector.user import User
from bot.actions.ej_connector.vote import Vote
import pytest

CONVERSATION_ID = "1"
COMMENT_ID = "1"
PHONE_NUMBER = "61992852776"
SENDER_ID = "mock_rasa_sender_id"


class TestAPIClass:
    """tests actions.ej_connector.api API class"""

    @patch("bot.actions.ej_connector.ej_api.requests.post")
    def test_create_user_in_ej_with_rasa_id(self, mock_post, tracker):
        mock_post.return_value = Mock(ok=True)
        user = User(tracker, "David")
        user.authenticate()
        assert user.ej_api.access_token == "1234"
        assert user.name == "David"

    @patch("bot.actions.ej_connector.ej_api.requests.get")
    def test_get_conversation(self, mock_get, tracker):
        response_value = {
            "text": "This is the conversation title",
            "links": {"self": "http://localhost:8000/api/v1/conversations/1/"},
        }
        mock_get.return_value = Mock(ok=True)
        mock_get.return_value.json.return_value = response_value
        response = Conversation.get_by_id(CONVERSATION_ID, tracker)
        assert response.get("text") == response_value["text"]

    @patch("bot.actions.ej_connector.ej_api.requests.get")
    def test_get_conversation_in_ej_invalid_response(self, mock_get, tracker):
        response_value = {}
        mock_get.return_value = Mock(ok=True)
        mock_get.return_value.json.return_value = response_value
        with pytest.raises(EJCommunicationError):
            Conversation.get_by_id(CONVERSATION_ID, tracker)

    @patch("bot.actions.ej_connector.ej_api.requests.get")
    def test_get_conversation_in_ej_forbidden_response(self, mock_get, tracker):
        mock_get.return_value = Mock(status=401), "forbidden"
        with pytest.raises(EJCommunicationError):
            Conversation.get_by_id(CONVERSATION_ID, tracker)

    @patch("bot.actions.ej_connector.ej_api.requests.get")
    def test_get_random_comment_in_ej(self, mock_get, tracker):
        response_value = {
            "content": "This is the comment text",
            "links": {"self": "http://localhost:8000/api/v1/comments/1/"},
        }
        mock_get.return_value = Mock(ok=True)
        mock_get.return_value.json.return_value = response_value
        conversation = Conversation(CONVERSATION_ID, "xpto", tracker)
        response = conversation.get_next_comment()
        assert response["content"] == response_value["content"]
        assert response["id"] == "1"

    @patch("bot.actions.ej_connector.ej_api.requests.get")
    def test_get_random_comment_in_ej_forbidden_response(self, mock_get, tracker):
        mock_get.return_value = Mock(status=401), "forbidden"
        with pytest.raises(EJCommunicationError):
            conversation = Conversation(CONVERSATION_ID, "xpto", tracker)
            conversation.get_next_comment()

    @patch("bot.actions.ej_connector.ej_api.requests.get")
    def test_get_user_conversation_statistics(self, mock_get, tracker):
        statistics_mock = {
            "votes": 3,
            "missing_votes": 6,
        }
        mock_get.return_value = Mock(ok=True)
        mock_get.return_value.json.return_value = statistics_mock
        conversation = Conversation(CONVERSATION_ID, "xpto", tracker)
        response = conversation.get_participant_statistics()
        assert response["votes"] == statistics_mock["votes"]
        assert response["missing_votes"] == statistics_mock["missing_votes"]

    @patch("bot.actions.ej_connector.ej_api.requests.get")
    def test_get_user_conversation_statistics_error_status(self, mock_get, tracker):
        mock_get.return_value = Mock(status=404), "not found"
        with pytest.raises(EJCommunicationError):
            conversation = Conversation(CONVERSATION_ID, "xpto", tracker)
            conversation.get_participant_statistics()

    @patch("bot.actions.ej_connector.vote.requests.post")
    def test_send_user_vote(self, mock_post, tracker):
        vote_response_mock = {"created": True}
        mock_post.return_value = Mock(ok=True)
        mock_post.return_value.json.return_value = vote_response_mock
        vote = Vote("0", tracker)
        response = vote.create(COMMENT_ID)
        assert response["created"]

    @patch("bot.actions.ej_connector.vote.requests.post")
    def test_send_user_vote_error_status(self, mock_post, tracker):
        mock_post.return_value = Mock(status=401), "forbidden"
        with pytest.raises(Exception):
            tracker = Mock()
            tracker.get_latest_input_channel = lambda: "foo"
            tracker.get_slot = lambda x: "foo"
            vote = Vote("0", tracker)
            vote.create(COMMENT_ID)

    @patch("bot.actions.ej_connector.comment.requests.post")
    def test_send_user_comment(self, mock_post, tracker):
        vote_response_mock = {"created": True, "content": "content"}
        mock_post.return_value = Mock(ok=True)
        mock_post.return_value.json.return_value = vote_response_mock

        comment = Comment(CONVERSATION_ID, "xpto", tracker)
        response = comment.create()
        assert response["created"]
        assert response["content"] == "content"

    @patch("bot.actions.ej_connector.comment.requests.post")
    def test_send_user_comment_error_status(self, mock_post, tracker):
        mock_post.return_value = Mock(status=404), "conversation not found"
        with pytest.raises(EJCommunicationError):
            comment = Comment(CONVERSATION_ID, "xpto", tracker)
            comment.create()

    @patch("bot.actions.ej_connector.ej_api.requests.get")
    def test_get_webchat_connection_to_conversation(self, mock_get, tracker):
        response_value = [
            {
                "conversation": "This is the conversation title",
                "links": {
                    "conversation": "http://localhost:8000/api/v1/conversations/1/"
                },
            }
        ]
        mock_get.return_value = Mock(ok=True)
        mock_get.return_value.json.return_value = response_value
        response = Conversation.get_by_bot_url("http://localhost:8000")
        assert response[0]["conversation"] == response_value[0]["conversation"]
        assert response[0]["links"]["conversation"][-2] == "1"

    @patch("bot.actions.ej_connector.ej_api.requests.get")
    def test_get_webchat_connection_not_existing(self, mock_get):
        mock_get.return_value = Mock(status=404), "conversation not found"
        with pytest.raises(EJCommunicationError):
            Conversation.get_by_bot_url("http://localhost:8000")


class TestEjUrlsGenerationClass:
    """tests bot.actions.ej_connector.api ej urls generation"""

    def test_conversation_url_generator(self):
        url = conversation_url(CONVERSATION_ID)
        assert url == f"{API_URL}/conversations/{CONVERSATION_ID}/"

    def test_conversation_random_comment_url_generator(self):
        url = conversation_random_comment_url(CONVERSATION_ID)
        assert url == f"{API_URL}/conversations/{CONVERSATION_ID}/random-comment/"

    def test_user_statistics_url_generator(self):
        url = user_statistics_url(CONVERSATION_ID)
        assert url == f"{API_URL}/conversations/{CONVERSATION_ID}/user-statistics/"

    def test_user_comments_route_generator(self):
        url = user_comments_route(CONVERSATION_ID)
        assert url == f"{API_URL}/conversations/{CONVERSATION_ID}/user-comments/"

    def test_user_pending_comments_route_generator(self):
        url = user_pending_comments_route(CONVERSATION_ID)
        assert (
            url == f"{API_URL}/conversations/{CONVERSATION_ID}/user-pending-comments/"
        )

import unittest
import pytest
from unittest.mock import Mock, MagicMock, patch
from bot.ej.ej_api import EjApi
from bot.ej.vote import Vote

from bot.ej.comment import Comment
from bot.ej.constants import *
from bot.ej.conversation import Conversation
from bot.ej.routes import *
from bot.ej.user import User
from bot.ej.vote import Vote

CONVERSATION_ID = "1"
COMMENT_ID = "1"
PHONE_NUMBER = "61992852776"
SENDER_ID = "mock_rasa_sender_id"


class TestEjApi(unittest.TestCase):
    def setUp(self):
        self.tracker = MagicMock()
        self.tracker.get_slot.side_effect = lambda x: (
            "test_token" if x == "access_token" else "refresh_token"
        )
        self.ej_api = EjApi(tracker=self.tracker)

    def test_initialization(self):
        self.assertEqual(self.ej_api.access_token, "test_token")
        self.assertEqual(self.ej_api.refresh_token, "refresh_token")

    def test_get_headers_with_access_token(self):
        headers = self.ej_api.get_headers()
        self.assertIn("Authorization", headers)

    def test_get_headers_without_access_token(self):
        self.tracker.get_slot.side_effect = lambda x: None
        headers = self.ej_api.get_headers()
        self.assertNotIn("Authorization", headers)

    @patch("requests.post")
    def test_refresh_access_token_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"access": "new_access_token"}
        mock_post.return_value = mock_response

        self.ej_api._refresh_access_token()
        self.assertEqual(self.ej_api.access_token, "new_access_token")
        self.tracker.update_slots.assert_called_once_with(
            {"access_token": "new_access_token"}
        )

    @patch("requests.post")
    def test_refresh_access_token_failure(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_post.return_value = mock_response

        with self.assertRaises(Exception):
            self.ej_api._refresh_access_token()

    @patch("requests.post")
    def test_post_request(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        response = self.ej_api._post(
            "http://example.com",
            {"Authorization": "Bearer test_token"},
            {"key": "value"},
        )
        self.assertEqual(response.status_code, 200)

    @patch("requests.get")
    def test_get_request(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        response = self.ej_api._get(
            "http://example.com", {"Authorization": "Bearer test_token"}
        )
        self.assertEqual(response.status_code, 200)

    @patch("requests.post")
    @patch("requests.get")
    def test_request_with_payload(self, mock_get, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        response = self.ej_api.request("http://example.com", {"key": "value"})
        self.assertEqual(response.status_code, 200)

    @patch("requests.post")
    @patch("requests.get")
    def test_request_without_payload(self, mock_get, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        response = self.ej_api.request("http://example.com")
        self.assertEqual(response.status_code, 200)

    @patch("requests.post")
    @patch("requests.get")
    def test_request_with_token_refresh(self, mock_get, mock_post):
        mock_response_401 = MagicMock()
        mock_response_401.status_code = 401
        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_post.side_effect = [mock_response_401, mock_response_200]

        self.ej_api._refresh_access_token = MagicMock()

        response = self.ej_api.request("http://example.com", {"key": "value"})
        self.assertEqual(response.status_code, 200)
        self.ej_api._refresh_access_token.assert_called_once()


class TestAPIClass:
    """tests ej.api API class"""

    @patch("bot.ej.ej_api.requests.post")
    def test_create_user_in_ej_with_rasa_id(self, mock_post, tracker):
        mock_post.return_value = Mock(ok=True)
        user = User(tracker)
        user.authenticate()
        assert user.ej_api.access_token == "1234"
        assert user.name == "mr_davidCarlos"

    @patch("bot.ej.ej_api.requests.get")
    def test_get_random_comment_in_ej(self, mock_get, tracker):
        response_value = {
            "content": "This is the comment text",
            "links": {"self": "http://localhost:8000/api/v1/comments/1/"},
        }
        mock_get.return_value = Mock(ok=True)
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = response_value
        conversation = Conversation(tracker)
        response = conversation.get_next_comment()
        assert response["content"] == response_value["content"]
        assert response["id"] == "1"

    @patch("bot.ej.ej_api.requests.get")
    def test_get_random_comment_in_ej_forbidden_response(self, mock_get, tracker):
        mock_get.return_value.status_code = 500
        with pytest.raises(EJCommunicationError):
            conversation = Conversation(tracker)
            conversation.get_next_comment()

    @patch("bot.ej.ej_api.requests.get")
    def test_get_user_conversation_statistics(self, mock_get, tracker):
        statistics_mock = {
            "votes": 3,
            "missing_votes": 6,
        }
        mock_get.return_value = Mock(ok=True)
        mock_get.return_value.json.return_value = statistics_mock
        conversation = Conversation(tracker)
        response = conversation.get_participant_statistics()
        assert response["votes"] == statistics_mock["votes"]
        assert response["missing_votes"] == statistics_mock["missing_votes"]

    @patch("bot.ej.ej_api.requests.get")
    def test_get_user_conversation_statistics_error_status(self, mock_get, tracker):
        mock_get.return_value = Mock(status=404), "not found"
        with pytest.raises(EJCommunicationError):
            conversation = Conversation(tracker)
            conversation.get_participant_statistics()

    @patch("bot.ej.vote.requests.post")
    def test_send_user_vote(self, mock_post, tracker):
        vote_response_mock = {"created": True}
        mock_post.return_value = Mock(ok=True)
        mock_post.return_value.json.return_value = vote_response_mock
        vote = Vote("0", tracker)
        response = vote.create(COMMENT_ID)
        assert response["created"]

    @patch("bot.ej.vote.requests.post")
    def test_send_user_vote_error_status(self, mock_post, tracker):
        mock_post.return_value = Mock(status=401), "forbidden"
        with pytest.raises(Exception):
            tracker = Mock()
            tracker.get_latest_input_channel = lambda: "foo"
            tracker.get_slot = lambda x: "foo"
            vote = Vote("0", tracker)
            vote.create(COMMENT_ID)

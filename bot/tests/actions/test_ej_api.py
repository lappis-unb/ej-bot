from unittest.mock import Mock, patch

import pytest

from bot.ej.comment import Comment
from bot.ej.settings import *
from bot.ej.conversation import Conversation, EJCommunicationError
from bot.ej.routes import *
from bot.ej.user import User
from bot.ej.vote import Vote

CONVERSATION_ID = "1"
COMMENT_ID = "1"
PHONE_NUMBER = "61992852776"
SENDER_ID = "mock_rasa_sender_id"


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

    @patch("bot.ej.comment.requests.post")
    def test_send_user_comment(self, mock_post, tracker):
        vote_response_mock = {"created": True, "content": "content"}
        mock_post.return_value = Mock(ok=True)
        mock_post.return_value.json.return_value = vote_response_mock

        comment = Comment(CONVERSATION_ID, "xpto", tracker)
        response = comment.create()
        assert response["created"]
        assert response["content"] == "content"

    @patch("bot.ej.comment.requests.post")
    def test_send_user_comment_error_status(self, mock_post, tracker):
        mock_post.return_value = Mock(status=404), "conversation not found"
        with pytest.raises(EJCommunicationError):
            comment = Comment(CONVERSATION_ID, "xpto", tracker)
            comment.create()


class TestEjUrlsGenerationClass:
    """tests bot.ej.api ej urls generation"""

    def test_conversation_url_generator(self):
        url = conversation_route(CONVERSATION_ID)
        assert url == f"{API_URL}/conversations/{CONVERSATION_ID}/"

    def test_conversation_random_comment_url_generator(self):
        url = random_comment_route(CONVERSATION_ID)
        assert url == f"{API_URL}/conversations/{CONVERSATION_ID}/random-comment/"

    def test_user_statistics_route_generator(self):
        url = user_statistics_route(CONVERSATION_ID)
        assert url == f"{API_URL}/conversations/{CONVERSATION_ID}/user-statistics/"

    def test_user_comments_route_generator(self):
        url = user_comments_route(CONVERSATION_ID)
        assert url == f"{API_URL}/conversations/{CONVERSATION_ID}/user-comments/"

    def test_user_pending_comments_route_generator(self):
        url = user_pending_comments_route(CONVERSATION_ID)
        assert (
            url == f"{API_URL}/conversations/{CONVERSATION_ID}/user-pending-comments/"
        )

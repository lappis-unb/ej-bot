import pytest
from unittest.mock import Mock, patch
from ej.ej_api import EjApi
from rasa_sdk import Tracker
from ej.conversation import Conversation, EJCommunicationError


class TestConversation:
    def test_user_should_not_authenticate_during_conversation(self, conversation):
        assert not conversation.user_should_authenticate(
            False, conversation.anonymous_votes_limit, {"comments": 4}
        )

    def test_user_should_authenticate_during_conversation(self, tracker, extra_data):
        conversation = Conversation(tracker, extra_data)
        assert conversation.user_should_authenticate(
            False, conversation.anonymous_votes_limit, {"comments": 5}
        )

    def test_init(self, conversation):
        assert conversation.id == "123"
        assert conversation.title == "Test Title"
        assert conversation.participant_can_add_comments
        assert conversation.anonymous_votes_limit == 5
        assert isinstance(conversation.ej_api, EjApi)

    def test_user_should_authenticate(self):
        statistics = {"comments": 5}
        assert Conversation.user_should_authenticate(False, 5, statistics)
        assert not Conversation.user_should_authenticate(True, 5, statistics)

    def test_available_comments_to_vote(self):
        statistics = {"missing_votes": 1}
        assert Conversation.available_comments_to_vote(statistics)
        statistics = {"missing_votes": 0}
        assert not Conversation.available_comments_to_vote(statistics)

    def test_get_total_comments(self):
        statistics = {"total_comments": 10}
        assert Conversation.get_total_comments(statistics) == 10

    def test_pause_to_ask_comment(self):
        assert Conversation.pause_to_ask_comment("PAUSA PARA PEDIR COMENTARIO")
        assert not Conversation.pause_to_ask_comment("OTHER VALUE")

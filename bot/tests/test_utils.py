import unittest

from bot.actions.ej_connector.comment import Comment

from .test_ej_connector import MockedTracker

from bot.actions.ej_connector.constants import *
from bot.actions.ej_connector.conversation import Conversation
from bot.actions.ej_connector.vote import Vote
from bot.actions.ej_connector.user import User


class UtilsTest(unittest.TestCase):
    def test_vote_values_list(self):
        values = ["1", "-1", "0"]
        assert values == VALID_VOTE_VALUES

    def test_stop_participation(self):
        assert Conversation.user_wants_to_stop_participation("parar") == True

    def test_vote_is_valid(self):
        mocked_tracker = MockedTracker()
        vote = Vote("1", mocked_tracker)
        assert vote.is_valid() == True

    def test_vote_is_invalid(self):
        mocked_tracker = MockedTracker()
        vote = Vote("xpto", mocked_tracker)
        assert vote.is_valid() == False

    def test_continue_voting(self):
        assert Vote.continue_voting() == {
            "vote": None,
            "comment_confirmation": None,
            "comment": None,
        }

    def test_stop_voting(self):
        assert Vote.stop_voting() == {"vote": "parar"}

    def test_finished_voting(self):
        mocked_tracker = MockedTracker()
        vote = Vote("Discordar", mocked_tracker)
        assert vote.finished_voting() == {"vote": "discordar"}

    def test_user_have_comments_to_vote(self):
        statistics = {"missing_votes": 5}
        assert Conversation.no_comments_left_to_vote(statistics) == False

    def test_define_vote_livechat(self):
        metadata = {"agent": "livechat"}
        message = "vote message"
        utter = Comment.get_utter(metadata, message)

        assert not "buttons" in utter
        assert "text" in utter
        assert message == utter["text"]

    def test_define_vote_channel_with_buttons(self):
        metadata = {"other_keys": " notlivechat"}
        message = "vote message"
        utter = Comment.get_utter(metadata, message)

        assert "buttons" in utter
        assert "text" in utter
        assert message == utter["text"]

    def test_remove_special(self):
        user = User("1234")
        assert ":" not in user.remove_special("sdf:adsf")
        assert "+" not in user.remove_special("sdf+adsf")
        assert "+" not in user.remove_special("sdf+:adsf")
        assert ":" not in user.remove_special("sdf+:adsf")

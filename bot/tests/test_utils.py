from bot.ej.comment import Comment, CommentDialogue

from bot.ej.constants import *
from bot.ej.conversation import Conversation
from bot.ej.vote import Vote, VoteDialogue
from bot.ej.user import User

TOKEN = "mock_token_value"


class TestUtils:
    def test_vote_values_list(self):
        values = ["1", "-1", "0"]
        assert values == VALID_VOTE_VALUES

    def test_vote_is_valid(self, tracker):
        vote = Vote("1", tracker)
        assert vote.is_valid() == True

    def test_vote_is_invalid(self, tracker):
        vote = Vote("xpto", tracker)
        assert vote.is_valid() == False

    def test_continue_voting(self, tracker):
        assert VoteDialogue.continue_voting(tracker) == {
            "vote": None,
            "comment_confirmation": None,
            "comment": None,
            "access_token": "1234",
            "refresh_token": "1234",
        }

    def test_finish_voting(self, tracker):
        vote = Vote("Discordar", tracker)
        assert VoteDialogue.finish_voting() == {
            "vote": "-",
            "comment_confirmation": "-",
            "comment": "-",
        }

    def test_user_have_comments_to_vote(self):
        statistics = {"missing_votes": 5}
        assert Conversation.no_comments_left_to_vote(statistics) == False

    def test_define_vote_livechat(self):
        metadata = {"agent": "livechat"}
        message = "vote message"
        utter = CommentDialogue.get_utter(metadata, message)

        assert not "buttons" in utter
        assert "text" in utter
        assert message == utter["text"]

    def test_define_vote_channel_with_buttons(self):
        metadata = {"other_keys": " notlivechat"}
        message = "vote message"
        utter = CommentDialogue.get_utter(metadata, message)

        assert "buttons" in utter
        assert "text" in utter
        assert message == utter["text"]

    def test_remove_special(self, tracker):
        user = User(tracker, "1234")
        assert ":" not in user.remove_special("sdf:adsf")
        assert "+" not in user.remove_special("sdf+adsf")
        assert "+" not in user.remove_special("sdf+:adsf")
        assert ":" not in user.remove_special("sdf+:adsf")

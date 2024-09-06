from bot.ej.comment import CommentDialogue
from rasa_sdk.events import SlotSet

from bot.ej.settings import *
from bot.ej.conversation import Conversation
from bot.ej.vote import SlotsType, Vote, VoteChoices, VoteDialogue
from bot.ej.user import User

TOKEN = "mock_token_value"


class TestUtils:
    def test_vote_values_list(self):
        values = ["1", "-1", "0"]
        assert VoteChoices(values[0])
        assert VoteChoices(values[1])
        assert VoteChoices(values[2])

    def test_vote_is_valid(self, tracker):
        vote = Vote("1", tracker)
        assert vote.is_valid()

    def test_vote_is_invalid(self, tracker):
        vote = Vote("xpto", tracker)
        assert vote.is_valid() == False

    def test_continue_voting(self, tracker):
        assert VoteDialogue.continue_voting(tracker) == {
            "vote": None,
            "access_token": "1234",
            "refresh_token": "5678",
        }

    def test_stop_voting(self, tracker):
        assert VoteDialogue.stop_voting() == {
            "vote": "-",
        }
        assert VoteDialogue.stop_voting(SlotsType.LIST) == [
            SlotSet("vote", "-"),
        ]

    def test_finish_voting(self, tracker):
        assert VoteDialogue.finish_voting(SlotsType.DICT) == {
            "vote": "-",
            "participant_voted_in_all_comments": True,
        }
        assert VoteDialogue.finish_voting(SlotsType.LIST) == [
            SlotSet("vote", "-"),
            SlotSet("participant_voted_in_all_comments", True),
        ]

    def test_user_have_comments_to_vote(self):
        statistics = {"missing_votes": 5}
        assert Conversation.available_comments_to_vote(statistics) == True

    def test_define_vote_livechat(self, livechat_metadata):
        message = "vote message"
        utter = CommentDialogue.get_utter_message(livechat_metadata, message, 1, 4)

        assert not "buttons" in utter
        assert "text" in utter

    def test_define_vote_channel_with_buttons(self, metadata):
        message = "vote message"
        utter = CommentDialogue.get_utter_message(metadata, message, 1, 4)

        assert "buttons" in utter
        assert "text" in utter

    def test_remove_special(self, tracker):
        user = User(tracker)
        assert ":" not in user.remove_special("sdf:adsf")
        assert "+" not in user.remove_special("sdf+adsf")
        assert "+" not in user.remove_special("sdf+:adsf")
        assert ":" not in user.remove_special("sdf+:adsf")

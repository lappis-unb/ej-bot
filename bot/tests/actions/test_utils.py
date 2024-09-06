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
        assert Vote.is_valid("1")

    def test_vote_is_invalid(self, tracker):
        vote = Vote("xpto", tracker)
        assert not Vote.is_valid("xpto")

    def test_continue_voting(self):
        assert VoteDialogue.restart_vote_form_slots() == {
            "vote": None,
        }

    def test_stop_voting(self, tracker):
        assert VoteDialogue.deactivate_vote_form_slots() == {
            "vote": "-",
        }
        assert VoteDialogue.deactivate_vote_form_slots(SlotsType.LIST) == [
            SlotSet("vote", "-"),
        ]

    def test_finish_voting(self, tracker):
        assert VoteDialogue.completed_vote_form_slots(SlotsType.DICT) == {
            "vote": "-",
            "participant_voted_in_all_comments": True,
        }
        assert VoteDialogue.completed_vote_form_slots(SlotsType.LIST) == [
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

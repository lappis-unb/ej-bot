from actions.checkers.vote_actions_checkers import (
    CheckEndConversationSlots,
    CheckExternalAutenticationSlots,
    CheckNextCommentSlots,
)
from actions.checkers.api_error_checker import EJApiErrorManager
from ej.vote import VoteDialogue
from ej.user import User


class TestCheckEndConversationSlots:
    def test_has_slots_to_return(self, tracker, dispatcher):
        user = User(tracker)
        checker = CheckEndConversationSlots(
            tracker=tracker,
            dispatcher=dispatcher,
            user=user,
            conversation_statistics={"missing_votes": 0},
        )
        assert checker.has_slots_to_return()
        assert checker.slots == VoteDialogue.finish_voting(format="slots")

    def test_should_not_return_slots_to_rasa(
        self, tracker, dispatcher, conversation_statistics
    ):

        user = User(tracker)
        checker = CheckEndConversationSlots(
            tracker=tracker,
            dispatcher=dispatcher,
            conversation_statistics=conversation_statistics,
            user=user,
        )
        assert not checker.has_slots_to_return()
        assert checker.slots == []


class TestCheckNextCommentSlots:
    def test_has_slots_to_return(
        self, tracker, dispatcher, conversation, conversation_statistics, comment
    ):
        checker = CheckNextCommentSlots(
            tracker=tracker,
            dispatcher=dispatcher,
            conversation=conversation,
            conversation_statistics=conversation_statistics,
        )
        assert checker.has_slots_to_return()
        assert checker.slots[1].get("value") == comment["content"]
        assert checker.slots[3].get("value") == comment["id"]


class TestCheckExternalAutenticationSlots:
    def test_has_slots_to_return(self, tracker, dispatcher, conversation_statistics):
        tracker.set_slot("anonymous_votes_limit", 2)
        conversation_statistics["comments"] = 2
        checker = CheckExternalAutenticationSlots(
            tracker=tracker,
            dispatcher=dispatcher,
            conversation_statistics=conversation_statistics,
        )
        assert checker.has_slots_to_return()
        assert checker.slots[0].get("value") == "-"
        assert checker.slots[1].get("value") == "-"
        assert checker.slots[2].get("value") == "-"


class TestEJApiErrorManager:
    def test_get_slots(self):
        ej_api_error_manager = EJApiErrorManager()
        slots = ej_api_error_manager.get_slots()
        assert slots[0].get("value") == "-"
        assert slots[1].get("value") == "-"
        assert slots[2].get("value") == "-"
        assert slots[3].get("value") == True

    def test_get_slots_as_dict(self):
        ej_api_error_manager = EJApiErrorManager()
        slots = ej_api_error_manager.get_slots(as_dict=True)
        assert slots.get("vote") == "-"
        assert slots.get("comment_confirmation") == "-"
        assert slots.get("comment") == "-"
        assert slots.get("ej_api_connection_error") == True

import pytest
from actions.checkers.vote_actions_checkers import (
    CheckRemainingCommentsSlots,
    CheckExternalAuthenticationSlots,
    CheckNextCommentSlots,
    CheckUserCanAddCommentsSlots,
)
from actions.checkers.api_error_checker import EJApiErrorManager
from ej.vote import SlotsType
from ej.user import User


class TestCheckRemainingCommentsSlots:
    def test_initialization(self, tracker, dispatcher, conversation_statistics):
        with pytest.raises(Exception):
            checker = CheckRemainingCommentsSlots(
                dispatcher=dispatcher,
                conversation_statistics={"missing_votes": 0},
                slots_type="foo",
            )
            checker.has_slots_to_return()

        conversation_statistics["missing_votes"] = 1
        checker = CheckRemainingCommentsSlots(
            dispatcher=dispatcher,
            conversation_statistics=conversation_statistics,
            slots_type=SlotsType.DICT,
        )

        assert checker.has_slots_to_return()
        assert type(checker.slots) == dict

        conversation_statistics["missing_votes"] = 0
        checker = CheckRemainingCommentsSlots(
            dispatcher=dispatcher,
            conversation_statistics=conversation_statistics,
            slots_type=SlotsType.LIST,
        )

        checker.set_slots()
        assert checker.has_slots_to_return()
        assert type(checker.slots) == list

    def test_keep_vote_form_running(self, tracker, dispatcher, conversation_statistics):
        conversation_statistics["missing_votes"] = 2

        checker = CheckRemainingCommentsSlots(
            dispatcher=dispatcher,
            conversation_statistics=conversation_statistics,
            slots_type=SlotsType.DICT,
        )

        assert checker.has_slots_to_return()
        assert checker.slots == {"vote": None}

    def test_completed_vote_form(self, tracker, dispatcher, conversation_statistics):
        conversation_statistics["missing_votes"] = 0

        checker = CheckRemainingCommentsSlots(
            dispatcher=dispatcher,
            conversation_statistics=conversation_statistics,
            slots_type=SlotsType.DICT,
        )

        assert checker.has_slots_to_return()
        assert checker.slots == {"vote": "-", "participant_voted_in_all_comments": True}


class TestCheckUserCanAddComentsSlots:
    def test_has_slots_to_return(self, tracker, dispatcher, conversation_statistics):
        tracker.set_slot("participant_can_add_comments", True)
        conversation_statistics["comments"] = 4

        checker = CheckUserCanAddCommentsSlots(
            tracker=tracker,
            dispatcher=dispatcher,
            conversation_statistics=conversation_statistics,
            slot_value="1",
        )

        assert checker.has_slots_to_return()
        assert checker.slots == {"vote": "1", "ask_for_a_comment": True}

    def test_has_no_slots_to_return(self, tracker, dispatcher, conversation_statistics):
        tracker.set_slot("participant_can_add_comments", True)
        conversation_statistics["comments"] = 5

        checker = CheckUserCanAddCommentsSlots(
            tracker=tracker,
            dispatcher=dispatcher,
            conversation_statistics=conversation_statistics,
            slot_value="1",
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


class TestCheckExternalAuthenticationSlots:
    def test_has_slots_to_return(self, tracker, dispatcher, conversation_statistics):
        tracker.set_slot("anonymous_votes_limit", 2)
        conversation_statistics["comments"] = 2
        checker = CheckExternalAuthenticationSlots(
            tracker=tracker,
            dispatcher=dispatcher,
            conversation_statistics=conversation_statistics,
            slots_type=SlotsType.LIST,
        )
        assert checker.has_slots_to_return()
        print(checker.slots)
        assert checker.slots[0].get("value") == "-"
        assert checker.slots[1].get("value") == True


class TestEJApiErrorManager:
    def test_get_slots(self):
        ej_api_error_manager = EJApiErrorManager()
        slots = ej_api_error_manager.get_slots()
        assert slots[0].get("value") == "-"
        assert slots[1].get("value") == True

    def test_get_slots_as_dict(self):
        ej_api_error_manager = EJApiErrorManager()
        slots = ej_api_error_manager.get_slots(as_dict=True)
        assert slots.get("vote") == "-"
        assert slots.get("ej_api_connection_error") == True

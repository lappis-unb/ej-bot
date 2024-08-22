from dataclasses import dataclass, field
from actions.checkers.api_error_checker import EJApiErrorManager
from ej.constants import EJCommunicationError
from ej.vote import VoteDialogue
from ej.profile import Profile
from rasa_sdk.events import FollowupAction, SlotSet
from typing import Any, List
from actions.logger import custom_logger


@dataclass
class CheckSlotsInterface:
    """
    Defines a common interface to verify an action slots.
    """

    tracker: Any = None
    dispatcher: Any = None
    slots: List[Any] = field(default_factory=list)
    slot_value: Any = None

    def should_return_slots_to_rasa(self) -> bool:
        """
        Returns True if the dialogue slots has to be updated.
        If True, the slots field must be updated with the corresponding SlotSet or FollowupAction.
        """
        raise Exception("not implemented")


@dataclass
class CheckNextProfileQuestionSlots(CheckSlotsInterface):
    """
    Request to EJ API the next comment to vote and update the user statistics slots.
    """

    def should_return_slots_to_rasa(self) -> bool:
        profile = Profile(self.tracker)

        try:
            message, id = profile.get_next_question()
        except EJCommunicationError:
            ej_api_error_manager = EJApiErrorManager()
            return ej_api_error_manager.get_slots()

        self._dispatch_messages(message)
        self._set_slots(id)
        return True

    def _dispatch_messages(self, message):
        if type(message) is str:
            self.dispatcher.utter_message(message)
        else:
            self.dispatcher.utter_message(**message)

    def _set_slots(self, id):
        self.slots = [
            SlotSet("profile_question_id", id),
            SlotSet("profile_question", "-"),
        ]


class CheckValidateProfileQuestion(CheckSlotsInterface):

    def should_return_slots_to_rasa(self) -> bool:
        profile = Profile(self.tracker)
        profile_question_id = self.tracker.get_slot("profile_question_id")

        if not profile.is_valid_answer(self.slot_value, profile_question_id):
            message = {
                "response": "utter_profile_fallback",
            }
            self._dispatch_messages(message)
            self._set_slots(is_valid=False)
        else:
            message = {
                "response": "utter_profile_received",
            }
            self._dispatch_messages(message)
            self._set_slots()

        return True

    def _dispatch_messages(self, message):
        if type(message) is str:
            self.dispatcher.utter_message(message)
        else:
            self.dispatcher.utter_message(**message)

    def _set_slots(self, is_valid=True):
        if is_valid:
            self.slots = [
                VoteDialogue.continue_voting(self.tracker),
                SlotSet("profile_question", self.slot_value),
                FollowupAction("vote_form"),
            ]
        else:
            self.slots = [
                SlotSet("profile_question", None),
            ]

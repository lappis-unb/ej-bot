from dataclasses import dataclass, field
from actions.checkers.api_error_checker import EJApiErrorManager
from actions.base_actions import CheckSlotsInterface
from ej.settings import EJCommunicationError
from ej.vote import VoteDialogue
from ej.profile import Profile
from rasa_sdk.events import SlotSet
from typing import Any, List


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
            SlotSet("profile_question", None),
        ]


class CheckValidateProfileQuestion(CheckSlotsInterface):
    def should_return_slots_to_rasa(self) -> bool:
        profile = Profile(self.tracker)
        profile_question_id = self.tracker.get_slot("profile_question_id")
        if profile_question_id:
            profile_question_id = int(profile_question_id)

        response, err = profile.is_valid_answer(self.slot_value, profile_question_id)

        if not response:
            if err:
                ej_api_error_manager = EJApiErrorManager()
                self.slots = ej_api_error_manager.get_slots(as_dict=True)
            else:
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
            self.slots = {
                **VoteDialogue.continue_voting(self.tracker),
                **Profile.finish_profile(self.slot_value),
            }
        else:
            self.slots = {
                **Profile.continue_profile(),
            }

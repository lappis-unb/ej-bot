from typing import Any, Dict, List, Text
from actions.logger import custom_logger
from actions.checkers.api_error_checker import EJApiErrorManager
from ej.constants import EJCommunicationError
from ej.profile import Profile
from rasa_sdk import Action, FormValidationAction, Tracker
from rasa_sdk.events import EventType, SlotSet
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict


class ActionAskProfileQuestion(Action):
    """
    https://rasa.com/docs/rasa/forms/#using-a-custom-action-to-ask-for-the-next-slot
    """

    def name(self) -> Text:
        return "action_ask_profile_question"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        profile = Profile(tracker)

        message = "no message"
        id = None
        try:
            message, id = profile.get_next_question()
        except EJCommunicationError:
            ej_api_error_manager = EJApiErrorManager()
            return ej_api_error_manager.get_slots()

        dispatcher.utter_message(message)

        return [SlotSet("profile_question_id", id)]


class ValidateProfileForm(FormValidationAction):
    """
    https://rasa.com/docs/rasa/forms/#validating-form-input
    """

    def name(self) -> Text:
        return "validate_profile_form"

    def validate_profile_question(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        profile = Profile(tracker)
        profile_question_id = tracker.get_slot("profile_question_id")
        if not profile.is_valid_answer(slot_value, profile_question_id):
            dispatcher.utter_message(template="utter_invalid_answer")
            return [SlotSet("profile_question", None)]

        return [SlotSet("profile_question", slot_value)]

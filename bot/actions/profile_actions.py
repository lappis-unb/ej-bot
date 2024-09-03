from typing import Any, Dict, List, Text

from actions.checkers.profile_actions_checkers import (
    CheckNextProfileQuestionSlots,
    CheckValidateProfileQuestion,
)
from actions.logger import custom_logger
from rasa_sdk import Action, Tracker
from rasa_sdk.events import EventType
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormValidationAction
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

        # If you want to add new verifications during this action call,
        # you need to implement a new Checker.
        action_checkers = self.get_checkers(
            tracker,
            dispatcher=dispatcher,
        )

        for checker in action_checkers:
            if checker.has_slots_to_return():
                self.slots = checker.slots
                break

        return self.slots

    def get_checkers(self, tracker, **kwargs) -> list:
        """
        Return a list of Checkers. They will be evaluated in sequence.
        """
        dispatcher = kwargs["dispatcher"]
        return [CheckNextProfileQuestionSlots(tracker=tracker, dispatcher=dispatcher)]


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
        custom_logger("validate_profile_question")
        custom_logger(f"slot_value: {slot_value}")

        if not slot_value:
            return {}

        action_checkers = self.get_checkers(
            tracker, dispatcher=dispatcher, slot_value=slot_value
        )

        for checker in action_checkers:
            if checker.has_slots_to_return():
                self.slots = checker.slots

        custom_logger(f"slots: {self.slots}")
        return self.slots

    def get_checkers(self, tracker, **kwargs) -> list:
        """
        Return a list of Checkers. They will be evaluated in sequence.
        """

        dispatcher = kwargs["dispatcher"]
        slot_value = kwargs["slot_value"]
        return [
            CheckValidateProfileQuestion(
                tracker=tracker, dispatcher=dispatcher, slot_value=slot_value
            )
        ]

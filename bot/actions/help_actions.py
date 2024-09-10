from enum import Enum
from typing import Any, Dict, Text

from actions.base_actions import CheckersMixin
from rasa_sdk import Action, FormValidationAction
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict


class ResetHelpFormSlots(Action):
    """
    Rest help_form slots to allows the user to request the help_form again.
    """

    def name(self):
        return "action_reset_help_slots"

    def run(self, dispatcher, tracker, domain):
        return [SlotSet("help_topic", None)]


class HelpChoices(Enum):
    """
    Enumerator with a list of valid help options.
    """

    HELP_VOTING = "utter_explain_help_voting"
    HELP_PLAN = "utter_explain_help_plan"
    HELP_KNOW_MORE = "utter_explain_help_know_more"
    HELP_AUTHENTICATION = "utter_explain_help_authentication"
    HELP_LGPD = "utter_explain_help_lgpd"


class ValidateHelpForm(FormValidationAction, CheckersMixin):
    """
    This action is called when the vote_form is active.
    It shows a comment for user to vote on, and also their statistics in the conversation.

    https://rasa.com/docs/rasa/forms/#using-a-custom-action-to-ask-for-the-next-slot
    """

    def name(self) -> Text:
        return "validate_help_form"

    def validate_help_topic(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:

        try:
            CHOICE = HelpChoices[slot_value.upper()]
            dispatcher.utter_message(response=CHOICE.value)
            return {"help_topic": slot_value}
        except Exception as e:
            raise e

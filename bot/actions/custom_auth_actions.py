from typing import Any, Dict, List, Text

from ej.conversation import Conversation
from ej.settings import EJCommunicationError
from ej.auth import CheckAuthenticationDialogue, ExternalAuthenticationManager
from ej.user import User
from rasa_sdk import Action, FormValidationAction, Tracker
from rasa_sdk.events import EventType
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict


class ValidateAuthenticationForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_authentication_form"

    def validate_has_completed_registration(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        return {}

    def validate_check_authentication(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        if not slot_value:
            return {}

        if CheckAuthenticationDialogue.participant_refuses_to_auth(slot_value):
            return CheckAuthenticationDialogue.end_auth_form()

        user = User(tracker)
        user.tracker.slots["access_token"] = ""
        user.tracker.slots["refresh_token"] = ""
        user.authenticate()

        if not user.has_completed_registration:
            dispatcher.utter_message(
                response="utter_error_during_authentication_validation"
            )
            return CheckAuthenticationDialogue.restart_auth_form()

        conversation = Conversation(user.tracker)
        return self._get_slots(user, conversation)

    def _get_slots(self, user: User, conversation: Conversation):
        return {
            "access_token": user.tracker.get_slot("access_token"),
            "refresh_token": user.tracker.get_slot("refresh_token"),
            "has_completed_registration": user.has_completed_registration,
            "conversation_text": conversation.text,
            "conversation_id": conversation.id,
        }


class ActionAskHasCompletedRegistration(Action):
    def name(self) -> Text:
        return "action_ask_check_authentication"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        try:
            user = User(tracker)
            authentication_manager = ExternalAuthenticationManager(
                tracker.sender_id, user.secret_id
            )
            auth_link = authentication_manager.get_authentication_link()
            message = CheckAuthenticationDialogue.get_message()
            dispatcher.utter_message(response="utter_get_token", auth_link=auth_link)
            dispatcher.utter_message(**message)

        except EJCommunicationError:
            dispatcher.utter_message(response="utter_ej_communication_error")
            return []

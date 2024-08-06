from typing import Any, Dict, List, Text

from ej.constants import EJCommunicationError
from ej.conversation import Conversation
from ej.user import (
    CheckAuthenticationDialogue,
    ExternalAuthorizationService,
    User,
)
from actions.logger import custom_logger
from rasa_sdk import Action, FormValidationAction, Tracker
from rasa_sdk.events import EventType, FollowupAction
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

        username = User.get_name_from_tracker_state(tracker.current_state())
        user = User(tracker, name=username)
        user.tracker.slots["access_token"] = ""
        user.tracker.slots["refresh_token"] = ""
        user.authenticate()

        if not user.has_completed_registration:
            dispatcher.utter_message(
                template="utter_error_during_authentication_validation"
            )
            return CheckAuthenticationDialogue.restart_auth_form()

        conversation_id = Conversation.get_id_from_tracker(user.tracker)
        conversation_data = Conversation.get_by_id(conversation_id, user.tracker)
        user.tracker.slots["conversation_text"] = conversation_data.get("text")
        user.tracker.slots["anonymous_votes_limit"] = conversation_data.get(
            "anonymous_votes_limit"
        )
        user.tracker.slots["participant_can_add_comments"] = conversation_data.get(
            "participants_can_add_comments"
        )
        conversation = Conversation(user.tracker)

        custom_logger(f"user: {user.auth_data()}")
        return self._get_slots(user, conversation)

    def _get_slots(self, user: User, conversation: Conversation):
        return {
            "access_token": user.tracker.get_slot("access_token"),
            "refresh_token": user.tracker.get_slot("refresh_token"),
            "has_completed_registration": user.has_completed_registration,
            "conversation_text": conversation.title,
            "conversation_id": conversation.id,
        }


class ActionAskHasCompletedRegistration(Action):
    def name(self) -> Text:
        return "action_ask_check_authentication"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        try:
            username = User.get_name_from_tracker_state(tracker.current_state())
            user = User(tracker, name=username)
            authorization_service = ExternalAuthorizationService(
                tracker.sender_id, user.secret_id
            )
            auth_link = authorization_service.get_authentication_link()
            message = CheckAuthenticationDialogue.get_message()
            dispatcher.utter_message(template="utter_get_token", auth_link=auth_link)
            dispatcher.utter_message(**message)

        except EJCommunicationError:
            dispatcher.utter_message(response="utter_ej_communication_error")
            dispatcher.utter_message(response="utter_error_try_again_later")
            return []

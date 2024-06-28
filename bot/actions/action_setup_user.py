import os

from actions.logger import custom_logger
from rasa_sdk import Action, Tracker
from rasa_sdk.events import FollowupAction, SlotSet
from rasa_sdk.executor import CollectingDispatcher

from .ej_connector import Conversation
from .ej_connector.user import User
from .ej_connector.constants import CONVERSATION_ID


class ActionSetupUser(Action):
    """
    Documentation
    """

    def name(self):
        return "action_setup_user"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict
    ) -> list:

        response = []

        custom_logger("Running action_setup_user")

        conversation_id = CONVERSATION_ID
        custom_logger(f"conversation_id: {conversation_id}")

        try:
            username = User.get_name_from_tracker_state(tracker.current_state())
            user = User(tracker, name=username)
            tracker_auth = user.authenticate()

            conversation_data = Conversation.get_by_id(conversation_id, tracker_auth)
            if not conversation_data:
                return self._dispatch_conversation_not_found(dispatcher)

            conversation_text = conversation_data.get("text")
            conversation = Conversation(conversation_id, tracker, conversation_text)
            response += self._set_conversation_slots(conversation)

            custom_logger(f"user: {user.serialize()}")
            response += self._set_user_slots(user)

            return response
        except:
            return self._dispatch_communication_error_with_ej(dispatcher)

    def _dispatch_communication_error_with_ej(self, dispatcher):
        dispatcher.utter_message(response="utter_ej_communication_error")
        dispatcher.utter_message(response="utter_error_try_again_later")
        return [FollowupAction("action_session_start")]

    def _dispatch_conversation_not_found(self, dispatcher):
        dispatcher.utter_message(response="utter_ej_connection_doesnt_exist")
        dispatcher.utter_message(response="utter_error_try_again_later")
        return [FollowupAction("action_session_start")]

    def _set_user_slots(self, user):
        response = [
            SlotSet("access_token", user.tracker.get_slot("access_token")),
            SlotSet("refresh_token", user.tracker.get_slot("refresh_token")),
            SlotSet("user_name", user.name),
            SlotSet("user_is_anonymous", user.anonymous),
        ]

        return response

    def _set_conversation_slots(self, conversation):
        response = [
            SlotSet("conversation_text", conversation.title),
            SlotSet("conversation_id", conversation.id),
        ]

        return response

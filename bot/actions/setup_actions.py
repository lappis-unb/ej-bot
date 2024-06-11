import os
from pathlib import Path

import yaml
from actions.logger import custom_logger

from rasa_sdk import Action
from rasa_sdk.events import FollowupAction, SlotSet

from .ej_connector import Conversation
from .ej_connector.user import User


class ActionGetConversation(Action):
    """
    Authenticates the chatbot user on EJ API and requests initial conversation data.
    This action is called on the beginner of every new conversation.
    """

    def name(self):
        return "action_get_conversation"

    def run(self, dispatcher, tracker, domain):
        self.response = []
        conversation_id = tracker.get_slot("conversation_id")
        if conversation_id:
            username = User.get_name_from_tracker_state(tracker.current_state())
            user = User(tracker, name=username)
            conversation_data = Conversation.get_by_id(conversation_id, user.tracker)
            conversation_text = conversation_data.get("text")
            conversation = Conversation(conversation_id, conversation_text, tracker)
            user.authenticate()
            self._set_slots_to_init_conversation(conversation, user)
        else:
            dispatcher.utter_message(template="utter_no_selected_conversation")
            return [FollowupAction("action_session_start")]
        return self.response

    def _dispatch_communication_error_with_ej(self, dispatcher):
        dispatcher.utter_message(template="utter_ej_communication_error")
        dispatcher.utter_message(template="utter_error_try_again_later")
        return [FollowupAction("action_session_start")]

    def _dispatch_conversation_not_found(self, dispatcher):
        dispatcher.utter_message(template="utter_ej_connection_doesnt_exist")
        dispatcher.utter_message(template="utter_error_try_again_later")
        return [FollowupAction("action_session_start")]

    def _set_slots_to_init_conversation(self, conversation, user):
        self.response = [
            SlotSet("conversation_text", conversation.title),
            SlotSet("conversation_id_cache", conversation.id),
            SlotSet("access_token", user.tracker.get_slot("access_token")),
            SlotSet("refresh_token", user.tracker.get_slot("refresh_token")),
        ]


class ActionIntroduceEj(Action):
    def name(self):
        return "action_introduce_ej"

    def run(self, dispatcher, tracker, domain):
        actions_path = os.path.dirname(os.path.realpath(__file__))
        path = Path(actions_path)
        messages = str(path.parent.absolute()) + "/messages.yml"
        text: str = ""
        with open(messages) as file:
            messages = yaml.safe_load(file)
            bot_name = os.getenv("BOT_NAME")
            if not bot_name:
                bot_name = "Default"
            text = messages.get(bot_name).get("introduction")
            dispatcher.utter_message(text=text)

        return []

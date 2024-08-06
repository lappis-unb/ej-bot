import os
from pathlib import Path

import yaml
from actions.checkers.api_error_checker import EJApiErrorManager
from ej.constants import EJCommunicationError

from rasa_sdk import Action
from rasa_sdk.events import FollowupAction, SlotSet

from ej.conversation import Conversation
from ej.user import User


class ActionGetConversation(Action):
    """
    Authenticates the chatbot user on EJ API and requests initial conversation data.
    This action is called on the beginner of every new conversation.
    """

    def name(self):
        return "action_get_conversation"

    def run(self, dispatcher, tracker, domain):
        self.slots = []
        conversation_id = tracker.get_slot("conversation_id")
        if conversation_id:
            username = User.get_name_from_tracker_state(tracker.current_state())
            user = User(tracker, name=username)

            try:
                conversation_data = Conversation.get_by_id(
                    conversation_id, user.tracker
                )
            except EJCommunicationError:
                ej_api_error_manager = EJApiErrorManager()
                return ej_api_error_manager.get_slots()

            tracker.slots["conversation_title"] = conversation_data.get("text")
            tracker.slots["anonymous_votes_limit"] = conversation_data.get(
                "anonymous_votes_limit"
            )
            tracker.slots["participant_can_add_comments"] = conversation_data.get(
                "participants_can_add_comments"
            )

            user.authenticate()

            conversation = Conversation(tracker)
            self._set_slots(conversation, user)
        else:
            dispatcher.utter_message(template="utter_no_selected_conversation")
            return [FollowupAction("action_session_start")]
        return self.slots

    def _dispatch_communication_error_with_ej(self, dispatcher):
        dispatcher.utter_message(template="utter_ej_communication_error")
        dispatcher.utter_message(template="utter_error_try_again_later")
        return [FollowupAction("action_session_start")]

    def _dispatch_conversation_not_found(self, dispatcher):
        dispatcher.utter_message(template="utter_ej_connection_doesnt_exist")
        dispatcher.utter_message(template="utter_error_try_again_later")
        return [FollowupAction("action_session_start")]

    def _set_slots(self, conversation: Conversation, user: User):
        self.slots = [
            SlotSet("conversation_text", conversation.title),
            SlotSet("conversation_id_cache", conversation.id),
            SlotSet("anonymous_votes_limit", conversation.anonymous_votes_limit),
            SlotSet(
                "participant_can_add_comments",
                conversation.participant_can_add_comments,
            ),
            SlotSet(
                "has_completed_registration",
                user.has_completed_registration,
            ),
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

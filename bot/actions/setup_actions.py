# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this gu"id"e on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions

from .ej_connector.user import User
import os
import logging

from rasa_sdk import Action
from rasa_sdk.events import SlotSet, FollowupAction
from .ej_connector import EJCommunicationError, Conversation
from .utils import *

logger = logging.getLogger(__name__)

from .setup_actions import *
from .comment_actions import *
from .vote_actions import *


# TODO: Rename to ActionGetConversation
class ActionSetupConversation(Action):
    """
    When in socketio channel:
        Send request to EJ with current URL where the bot is hosted
        Get conversation ID and Title in return
    When in other channels:
        Get already set slot conversation id and send it to EJ
        to get corresponding conversation title
    """

    def name(self):
        return "action_setup_conversation"

    def run(self, dispatcher, tracker, domain):
        self.response = []
        if tracker.get_latest_input_channel() == "socketio":
            bot_url = tracker.get_slot("url")
            try:
                conversation_data = Conversation.get_by_bot_url(bot_url)
                if conversation_data:
                    user = User(tracker.sender_id)
                    user.authenticate()
                    conversation_text = conversation_data.get("conversation").get(
                        "text"
                    )
                    conversation_id = conversation_data.get("conversation").get("id")
                    conversation = Conversation(
                        conversation_id, conversation_text, user.token
                    )
                    self._set_slots_to_init_conversation(conversation, user)
                else:
                    self._dispatch_conversation_not_found(dispatcher)
            except EJCommunicationError:
                self._dispatch_communication_error_with_ej(dispatcher)
        else:
            conversation_id = tracker.get_slot("conversation_id")
            if conversation_id:
                username = User.get_name_from_tracker_state(tracker.current_state())
                user = User(tracker.sender_id, name=username)
                user.authenticate()
                conversation_data = Conversation.get_by_id(conversation_id)
                conversation_text = conversation_data.get("text")
                conversation = Conversation(
                    conversation_id, conversation_text, user.token
                )
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
        statistics = conversation.get_participant_statistics()
        first_comment = conversation.get_next_comment()
        self.response = [
            SlotSet("conversation_text", conversation.title),
            SlotSet("conversation_id", conversation.id),
            SlotSet("conversation_id_cache", conversation.id),
            SlotSet("number_voted_comments", statistics["votes"]),
            SlotSet(
                "number_comments", statistics["missing_votes"] + statistics["votes"]
            ),
            SlotSet("comment_text", first_comment["content"]),
            SlotSet("current_comment_id", first_comment["id"]),
            SlotSet("ej_user_token", user.token),
        ]


class ActionSetChannelInfo(Action):
    """
    Rasa set current user channel on tracker.get_latest_input_channel()
    but it cannot read nuances such as:
        - Being on a private or group chat on telegram or rocketchat
        - Being on rocketchat livechat or any other kind of chat
    This kind of data is set on message metadata, and we access it to
    set current channel with more detail
    """

    def name(self):
        return "action_set_channel_info"

    def run(self, dispatcher, tracker, domain):
        logger.debug("action ActionSetChannelInfo called")
        channel = tracker.get_latest_input_channel()
        if tracker.get_latest_input_channel() == "rocketchat":
            if "agent" in tracker.latest_message["metadata"]:
                channel = "rocket_livechat"
        if tracker.get_latest_input_channel() == "telegram":
            bot_telegram_username = os.getenv("TELEGRAM_BOT_NAME")
            return [
                SlotSet("current_channel_info", channel),
                SlotSet("bot_telegram_username", bot_telegram_username),
            ]
        if tracker.get_latest_input_channel() == "twilio":
            bot_whatsapp_number = os.getenv("TWILIO_WHATSAPP")

            return [
                SlotSet("current_channel_info", channel),
                SlotSet("bot_whatsapp_number", number_from_wpp(bot_whatsapp_number)),
            ]

        return [
            SlotSet("current_channel_info", channel),
        ]

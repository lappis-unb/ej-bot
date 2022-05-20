from rasa_sdk import Action
import logging

from .ej_connector.comment import Comment
from .utils import *

logger = logging.getLogger(__name__)


class ActionSetNewComment(Action):
    def name(self):
        return "action_set_new_comment"

    def run(self, dispatcher, tracker, domain):
        logger.debug("action ActionSetNewComment called")
        conversation_id = tracker.get_slot("conversation_id_cache")
        token = tracker.get_slot("ej_user_token")
        comment_text = tracker.latest_message["text"]
        comment = Comment(conversation_id, comment_text, token)
        try:
            last_intent = tracker.latest_message["intent"].get("name")
            if last_intent == "add_new_comment":
                comment.create()
                dispatcher.utter_message(template="utter_sent_comment")
        except:
            dispatcher.utter_message(template="utter_send_comment_error")


class ActionCustomizedFallback(Action):
    def name(self):
        return "action_customized_fallback"

    def run(self, dispatcher, tracker, domain):
        logger.debug("action ActionCustomizedFallback called")

        if self.get_last_action(tracker) in [
            "utter_ask_to_add_comment",
        ]:
            dispatcher.utter_message(template="utter_comment_fallback")
        else:
            dispatcher.utter_message(template="utter_help")

    def get_last_action(self, tracker):
        for event in reversed(tracker.events):
            if event.get("name") not in ["action_listen", None, "conversation_id"]:
                return event.get("name")
        return None

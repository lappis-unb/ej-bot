import logging
from rasa_sdk import Action
from rasa_sdk.events import SlotSet, FollowupAction

from .ej_connector.conversation import Conversation
from .utils import *

logger = logging.getLogger(__name__)


class ActionFollowUpForm(Action):
    """
    ActionFollowUpForm is called after an user vote.
    It validates the next bot step based on user vote value.
    This action is called after every vote.
    """

    def name(self):
        return "action_follow_up_form"

    def run(self, dispatcher, tracker, domain):
        logger.debug("action ActionFollowUpForm called")
        vote = tracker.get_slot("vote")
        self.response = []

        self._dispatch_if_stop_participation(dispatcher, vote)
        self._set_response_to_ask_comment(vote)
        self._set_response_to_starts_new_conversation(vote)
        self._set_response_to_continue_conversation(vote)
        return self.response

    def _dispatch_if_stop_participation(self, dispatcher, vote):
        if Conversation.user_wants_to_stop_participation(vote):
            dispatcher.utter_message(template="utter_thanks_participation")
            dispatcher.utter_message(template="utter_stopped")

    def _set_response_to_ask_comment(self, vote):
        if Conversation.pause_to_ask_comment(vote):
            self.response = [
                SlotSet("vote", None),
                FollowupAction("utter_ask_to_add_comment"),
            ]

    def _set_response_to_starts_new_conversation(self, vote):
        if Conversation.is_vote_on_new_conversation(vote):
            self.response = [
                SlotSet("vote", None),
                FollowupAction("action_setup_conversation"),
            ]

    def _set_response_to_continue_conversation(self, vote):
        if not self.response and vote == None:
            self.response = [
                SlotSet("vote", None),
                SlotSet("conversation_id", None),
            ]

import os
from pathlib import Path
import random
from typing import Dict

from actions.checkers.api_error_checker import EJApiErrorManager
from actions.logger import custom_logger
from ej.constants import EJCommunicationError

from rasa_sdk import Action
from rasa_sdk.events import FollowupAction, SlotSet

from actions.logger import custom_logger

from ej.boards import Board
from ej.conversation import Conversation
from ej.user import User
from rasa_sdk import Action
from rasa_sdk.events import SlotSet


class ResetHelpFormSlots(Action):
    """
    Rest help_form slots to allows the user to request the help_form again.
    """

    def name(self):
        return "action_reset_help_slots"

    def run(self, dispatcher, tracker, domain):
        return [SlotSet("help_topic", None)]


class ActionGetConversation(Action):
    """
    Authenticates the chatbot user on EJ API and requests initial conversation data.
    This action is called on the beginner of every new conversation.
    """

    def name(self):
        return "action_get_conversation"

    # TODO: refactors this method using the Checkers architecture.
    # Use ActionAskVote as an example.
    def run(self, dispatcher, tracker, domain):
        user = User(tracker)
        user.authenticate()
        tracker = user.tracker

        self.slots = []
        board_id = int(os.getenv("BOARD_ID", None))

        if not board_id:
            dispatcher.utter_message(template="utter_no_board_id")
            raise Exception("No board id provided.")

        board = Board(board_id, tracker)
        total_conversations = len(board.conversations)

        if total_conversations == 0:
            dispatcher.utter_message(template="utter_no_conversations")
            raise Exception("No conversations found.")

        index = 0

        conversation = board.conversations[index]

        self._set_slots(conversation, user)

        return self.slots

    def _set_slots(self, conversation: Conversation, user: User):
        self.slots = [
            SlotSet("conversation_id", conversation.id),
            SlotSet("conversation_title", conversation.title),
            SlotSet("conversation_text", conversation.title),
            SlotSet("conversation_id_cache", conversation.id),
            SlotSet("anonymous_votes_limit", conversation.anonymous_votes_limit),
            SlotSet(
                "participant_can_add_comments",
                conversation.participant_can_add_comments,
            ),
            SlotSet("contact_name", user.name),
            SlotSet(
                "has_completed_registration",
                user.has_completed_registration,
            ),
            SlotSet("access_token", user.tracker.get_slot("access_token")),
            SlotSet("refresh_token", user.tracker.get_slot("refresh_token")),
        ]

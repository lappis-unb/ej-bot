import os
from pathlib import Path
import random
import redis

import yaml
from actions.checkers.api_error_checker import EJApiErrorManager
from ej.constants import EJCommunicationError

from rasa_sdk import Action
from rasa_sdk.events import FollowupAction, SlotSet

from ej.conversation import Conversation
from ej.user import User
from ej.boards import Board
from ej.redis_manager import RedisManager


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
        self.slots = []
        board_id = os.getenv("BOARD_ID", None)
        get_random_conversation = os.getenv("GET_RANDOM_CONVERSATION", False)

        if not board_id:
            dispatcher.utter_message(template="utter_no_board_id")
            raise Exception("No board id provided.")

        board = Board(board_id, tracker)
        total_conversations = len(board.conversations)

        if total_conversations == 0:
            dispatcher.utter_message(template="utter_no_conversations")
            raise Exception("No conversations found.")

        redis_manager = RedisManager()

        index = redis_manager.get_user_conversation(tracker.sender_id)

        if not index:
            if get_random_conversation:
                index = random.randint(0, total_conversations - 1)
            else:
                index = 0

        conversation = board.conversations[index]

        username = User.get_name_from_tracker_state(tracker.current_state())
        user = User(tracker, name=username)
        user.authenticate()

        conversation = Conversation(tracker)
        self._set_slots(conversation, user)

        return self.slots

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

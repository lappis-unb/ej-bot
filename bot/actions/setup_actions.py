import os
from actions.checkers.api_error_checker import EJApiErrorManager
from ej.settings import EJCommunicationError

from rasa_sdk import Action
from rasa_sdk.events import SlotSet

from ej.boards import Board
from ej.conversation import Conversation
from ej.user import ExternalAuthorizationService, User
from rasa_sdk import Action
from rasa_sdk.events import SlotSet


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

        self.slots = []
        board_id = os.getenv("BOARD_ID", None)
        conversation_id = os.getenv("CONVERSATION_ID", None)

        if conversation_id is not None:
            try:
                conversation_data = Conversation.get(int(conversation_id), user.tracker)
                conversation = Conversation(user.tracker, conversation_data)
                self._set_slots(conversation, user)
                return self.slots
            except EJCommunicationError:
                ej_api_error_manager = EJApiErrorManager()
                return ej_api_error_manager.get_slots()

        if board_id is None:
            dispatcher.utter_message(template="utter_no_board_id")
            raise Exception("No board id provided.")

        try:
            board = Board(int(board_id), user.tracker)
        except EJCommunicationError:
            ej_api_error_manager = EJApiErrorManager()
            return ej_api_error_manager.get_slots()

        total_conversations = len(board.conversations)
        if total_conversations == 0:
            dispatcher.utter_message(template="utter_no_conversations")
            raise Exception("No conversations found.")

        index = 0
        conversation = board.conversations[index]
        self._set_slots(conversation, user)
        return self.slots

    def _set_slots(self, conversation: Conversation, user: User):
        authorization_service = ExternalAuthorizationService(
            user.tracker.sender_id, user.secret_id
        )
        auth_link = authorization_service.get_authentication_link()

        self.slots = [
            SlotSet("auth_link", auth_link),
            SlotSet("conversation_id", conversation.id),
            SlotSet("conversation_text", conversation.text),
            SlotSet("anonymous_votes_limit", conversation.anonymous_votes_limit),
            SlotSet(
                "participant_can_add_comments",
                conversation.participant_can_add_comments,
            ),
            SlotSet("send_profile_questions", conversation.send_profile_question),
            SlotSet(
                "votes_to_send_profile_questions",
                conversation.votes_to_send_profile_questions,
            ),
            SlotSet("contact_name", user.name),
            SlotSet(
                "has_completed_registration",
                user.has_completed_registration,
            ),
            SlotSet("access_token", user.tracker.get_slot("access_token")),
            SlotSet("refresh_token", user.tracker.get_slot("refresh_token")),
        ]

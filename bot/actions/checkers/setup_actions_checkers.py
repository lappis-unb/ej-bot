from dataclasses import dataclass
from actions.checkers.api_error_checker import EJClientErrorManager
from actions.checkers.profile_actions_checkers import CheckSlotsInterface
from ej.boards import Board
from ej.user import ExternalAuthenticationManager, User
from ej.settings import EJCommunicationError
from ej.conversation import Conversation
from rasa_sdk.events import SlotSet

from ej.settings import EJCommunicationError, BOARD_ID, CONVERSATION_ID


def get_slots(conversation: Conversation, user: User):
    authentication_manager = ExternalAuthenticationManager(
        user.tracker.sender_id, user.secret_id
    )
    return [
        SlotSet("auth_link", authentication_manager.get_authentication_link()),
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


@dataclass
class CheckGetConversationSlots(CheckSlotsInterface):
    def has_slots_to_return(self) -> bool:
        """ """
        if CONVERSATION_ID is not None:
            try:
                conversation_data = Conversation.get(
                    int(CONVERSATION_ID), self.user.tracker
                )
                conversation = Conversation(self.user.tracker, conversation_data)
                self.set_slots(conversation)
            except EJCommunicationError:
                ej_client_error_manager = EJClientErrorManager()
                self.slots = ej_client_error_manager.get_slots()
            return True
        return False

    def set_slots(self, conversation: Conversation):
        self.slots = get_slots(conversation, self.user)


@dataclass
class CheckGetBoardSlots(CheckSlotsInterface):
    def has_slots_to_return(self) -> bool:
        """ """
        ej_client_error_manager = EJClientErrorManager()

        if BOARD_ID is None:
            self.dispatcher.utter_message(response="utter_no_board_id")
            self.slots = ej_client_error_manager.get_slots()
            return True

        try:
            board = Board(int(BOARD_ID), self.user.tracker)
            if len(board.conversations) == 0:
                self.dispatcher.utter_message(response="utter_no_conversations")
                raise Exception("No conversations found.")

            index = 0
            conversation = board.conversations[index]
            self.set_slots(conversation)
            return self.slots
        except EJCommunicationError:
            self.slots = ej_client_error_manager.get_slots()

        return True

    def set_slots(self, conversation: Conversation):
        self.slots = get_slots(conversation, self.user)

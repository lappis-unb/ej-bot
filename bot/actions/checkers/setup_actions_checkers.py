from dataclasses import dataclass
from actions.checkers.api_error_checker import EJApiErrorManager
from actions.checkers.profile_actions_checkers import CheckSlotsInterface
from ej.boards import Board
from ej.user import ExternalAuthorizationService, User
from ej.settings import EJCommunicationError
from ej.conversation import Conversation
from rasa_sdk.events import SlotSet

from ej.settings import EJCommunicationError, BOARD_ID, CONVERSATION_ID


def get_slots(conversation: Conversation, user: User, conversation_statistics: dict):
    authorization_service = ExternalAuthorizationService(
        user.tracker.sender_id, user.secret_id
    )
    return [
        SlotSet("conversation_statistics", conversation_statistics),
        SlotSet("auth_link", authorization_service.get_authentication_link()),
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
    def should_return_slots_to_rasa(self) -> bool:
        """ """
        if CONVERSATION_ID is not None:
            try:
                conversation_data = Conversation.get(
                    int(CONVERSATION_ID), self.user.tracker
                )
                conversation = Conversation(self.user.tracker, conversation_data)
                conversation_statistics = conversation.get_participant_statistics()
                self.set_slots(conversation, conversation_statistics)
            except EJCommunicationError:
                ej_api_error_manager = EJApiErrorManager()
                self.slots = ej_api_error_manager.get_slots()
            return True
        return False

    def set_slots(self, conversation: Conversation, conversation_statistics: dict):
        self.slots = get_slots(conversation, self.user, conversation_statistics)


@dataclass
class CheckGetBoardSlots(CheckSlotsInterface):
    def should_return_slots_to_rasa(self) -> bool:
        """ """
        ej_api_error_manager = EJApiErrorManager()

        if BOARD_ID is None:
            self.dispatcher.utter_message(template="utter_no_board_id")
            self.slots = ej_api_error_manager.get_slots()
            return True

        try:
            board = Board(int(BOARD_ID), self.user.tracker)
            if len(board.conversations) == 0:
                self.dispatcher.utter_message(template="utter_no_conversations")
                raise Exception("No conversations found.")

            index = 0
            conversation = board.conversations[index]
            conversation_statistics = conversation.get_participant_statistics()
            self.set_slots(conversation, conversation_statistics)
            return self.slots
        except EJCommunicationError:
            self.slots = ej_api_error_manager.get_slots()

        return True

    def set_slots(self, conversation: Conversation, conversation_statistics: dict):
        self.slots = get_slots(conversation, self.user, conversation_statistics)

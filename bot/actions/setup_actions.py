from actions.checkers.setup_actions_checkers import (
    CheckGetBoardSlots,
    CheckGetConversationSlots,
)
from actions.checkers.vote_actions_checkers import CheckUserCompletedConversationSlots
from ej.vote import SlotsType
from ej.user import User
from rasa_sdk import Action


class ActionGetConversation(Action):
    """
    Authenticates the chatbot user on EJ API and requests initial conversation data.
    This action is called on the beginner of every new conversation.
    """

    def name(self):
        return "action_get_conversation"

    def run(self, dispatcher, tracker, domain):
        user = User(tracker)
        user.authenticate()

        self.slots = []

        checkers = self.get_checkers(tracker, user=user, dispatcher=dispatcher)
        for checker in checkers:
            if checker.has_slots_to_return():
                self.slots = checker.slots
                break

        return self.slots

    def get_checkers(self, tracker, **kwargs) -> list:
        dispatcher = kwargs["dispatcher"]
        user = kwargs["user"]
        return [
            CheckGetConversationSlots(
                dispatcher=dispatcher, user=user, slots_type=SlotsType.LIST
            ),
            CheckGetBoardSlots(
                dispatcher=dispatcher, user=user, slots_type=SlotsType.LIST
            ),
            CheckUserCompletedConversationSlots(
                tracker=tracker,
                dispatcher=dispatcher,
                user=user,
                slots_type=SlotsType.LIST,
            ),
        ]

from typing import Any, Dict, List, Text

from actions.base_actions import CheckersMixin
from actions.checkers.api_error_checker import EJApiErrorManager
from actions.checkers.vote_actions_checkers import (
    CheckEndConversationSlots,
    CheckExternalAutenticationSlots,
    CheckNeedToAskAboutProfile,
    CheckNextCommentSlots,
)
from actions.logger import custom_logger
from ej.user import User
from ej.comment import CommentDialogue
from ej.conversation import Conversation
from ej.settings import EJCommunicationError
from ej.vote import Vote, VoteDialogue
from rasa_sdk import Action, FormValidationAction, Tracker
from rasa_sdk.events import EventType
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict


class ActionAskComment(Action, CheckersMixin):
    """
    This action is called when the vote_form is active.
    It shows a comment for user to vote on, and also their statistics in the conversation.

    https://rasa.com/docs/rasa/forms/#using-a-custom-action-to-ask-for-the-next-slot
    """

    def name(self) -> Text:
        return "action_ask_comment"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        dispatcher.utter_message(template="utter_ask_comment")
        return []


class ActionAskVote(Action, CheckersMixin):
    """
    This action is called when the vote_form is active.
    It shows a comment for user to vote on, and also their statistics in the conversation.

    https://rasa.com/docs/rasa/forms/#using-a-custom-action-to-ask-for-the-next-slot
    """

    def name(self) -> Text:
        return "action_ask_vote"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        user = User(tracker)
        conversation = Conversation(tracker)
        try:
            conversation_statistics = conversation.get_participant_statistics()
        except EJCommunicationError:
            ej_api_error_manager = EJApiErrorManager()
            return ej_api_error_manager.get_slots()

        # If you want to add new verifications during this action call,
        # you need to implement a new Checker.
        action_chekers = self.get_checkers(
            tracker,
            dispatcher=dispatcher,
            conversation=conversation,
            conversation_statistics=conversation_statistics,
            user=user,
        )

        for checker in action_chekers:
            if checker.has_slots_to_return():
                custom_logger(checker, _type="string")
                self.slots = checker.slots
                break

        return self.slots

    def get_checkers(self, tracker, **kwargs) -> list:
        """
        Return a list of Checkers. They will be evaluated in sequence.
        """
        dispatcher = kwargs["dispatcher"]
        conversation = kwargs["conversation"]
        user = kwargs["user"]
        conversation_statistics = kwargs["conversation_statistics"]
        return [
            CheckEndConversationSlots(
                tracker=tracker,
                dispatcher=dispatcher,
                user=user,
                conversation_statistics=conversation_statistics,
            ),
            CheckExternalAutenticationSlots(
                tracker=tracker,
                dispatcher=dispatcher,
                conversation_statistics=conversation_statistics,
            ),
            CheckNeedToAskAboutProfile(
                tracker=tracker,
                dispatcher=dispatcher,
                conversation=conversation,
                conversation_statistics=conversation_statistics,
            ),
            CheckNextCommentSlots(
                tracker=tracker,
                dispatcher=dispatcher,
                conversation=conversation,
                conversation_statistics=conversation_statistics,
            ),
        ]


class ValidateVoteForm(FormValidationAction):
    """
    This action is called when the vote form is active.
    After ActionAskVote ran, action_listen is activated and user should input.
    This action validates what user typed

    If the returned vote value is None, Rasa will call ActionAskVote again until a
    not-null value is returned by this action. This will assure that the chatbot keeps
    sending new comments to vote.

    https://rasa.com/docs/rasa/forms/#validating-form-input
    """

    def name(self) -> Text:
        return "validate_vote_form"

    # TODO: refactors this method using the Checkers architecture.
    # Use ActionAskVote as an example.
    def validate_vote(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate vote value."""

        if not slot_value:
            return {}

        ej_api_error_manager = EJApiErrorManager()
        conversation = Conversation(tracker)

        vote = Vote(slot_value, tracker)
        if vote.is_valid():
            custom_logger(f"POST vote to EJ API: {vote}")
            try:
                vote.create(tracker.get_slot("current_comment_id"))
            except EJCommunicationError:
                return ej_api_error_manager.get_slots(as_dict=True)
            self._dispatch_save_participant_vote(dispatcher, {"created": "ok"})

            try:
                statistics = conversation.get_participant_statistics()
            except EJCommunicationError:
                return ej_api_error_manager.get_slots(as_dict=True)

            if Conversation.user_can_add_comment(statistics, tracker):
                custom_logger(
                    f"TIME TO ASK COMMENT {CommentDialogue.deactivate_vote_form(slot_value)}"
                )
                return CommentDialogue.deactivate_vote_form(slot_value)
            return self._dispatch_show_next_comment(
                dispatcher, statistics, vote, tracker
            )
        else:
            try:
                statistics = conversation.get_participant_statistics()
            except EJCommunicationError:
                return ej_api_error_manager.get_slots(as_dict=True)
            if vote.is_internal():
                return self._dispatch_show_next_comment(
                    dispatcher, statistics, vote, tracker
                )
            dispatcher.utter_message(template="utter_invalid_vote_during_participation")
            return VoteDialogue.continue_voting(tracker)

    def _dispatch_save_participant_vote(self, dispatcher, vote_data):
        if vote_data.get("created"):
            dispatcher.utter_message(template="utter_vote_received")

    def _dispatch_show_next_comment(
        self, dispatcher, statistics, vote: Vote, tracker: Tracker
    ):
        if Conversation.available_comments_to_vote(statistics):
            return VoteDialogue.continue_voting(tracker)
        else:
            return VoteDialogue.finish_voting()

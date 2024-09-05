from typing import Any, Dict, List, Text

from actions.base_actions import CheckersMixin
from actions.logger import custom_logger
from ej.comment import Comment, CommentDialogue
from ej.conversation import Conversation
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


class ValidateCommentForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_comment_form"

    def validate_comment_confirmation(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        if CommentDialogue.user_refuses_to_add_comment(slot_value):
            return CommentDialogue.deactivate_comment_form()
        return {"comment_confirmation": slot_value}

    # TODO: refactors this method using the Checker architecture.
    # Use ActionAskVote as an example.
    def validate_comment(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        user_comment = slot_value
        conversation_id = tracker.get_slot("conversation_id")
        comment = Comment(conversation_id, user_comment, tracker)

        try:
            comment.create()
            dispatcher.utter_message(template="utter_sent_comment")
            return {"vote": None}
        except:
            dispatcher.utter_message(template="utter_send_comment_error")

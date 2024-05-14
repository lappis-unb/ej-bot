from typing import Any, Dict, List, Text

from actions.logger import custom_logger
from rasa_sdk import Action, FormValidationAction, Tracker
from rasa_sdk.events import EventType, FollowupAction, SlotSet
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict

from .ej_connector import EJCommunicationError
from .ej_connector.comment import Comment
from .ej_connector.conversation import Conversation
from .ej_connector.vote import Vote


class ActionAskVote(Action):
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
        conversation_id = tracker.get_slot("conversation_id_cache")
        conversation_text = tracker.get_slot("conversation_text")
        token = tracker.get_slot("ej_user_token")
        channel = tracker.get_latest_input_channel()
        conversation = Conversation(conversation_id, conversation_text, token)
        conversation_statistics = conversation.get_participant_statistics()
        if Conversation.no_comments_left_to_vote(conversation_statistics):
            return self._dispatch_user_vote_on_all_comments(dispatcher)
        try:
            comment = conversation.get_next_comment()
            custom_logger(f"Send {comment} to {channel} user")
            return self._dispatch_comment_to_vote(
                dispatcher, conversation_statistics, comment, channel, tracker
            )
        except EJCommunicationError:
            return self._dispatch_errors(dispatcher)

    def _dispatch_errors(self, dispatcher):
        dispatcher.utter_message(template="utter_ej_communication_error")
        dispatcher.utter_message(template="utter_error_try_again_later")
        return [FollowupAction("action_session_start")]

    def _dispatch_comment_to_vote(
        self, dispatcher, conversation_statistics, comment, channel, tracker
    ) -> List:
        metadata = tracker.latest_message.get("metadata")
        total_comments = Conversation.get_total_comments(conversation_statistics)
        current_comment = Conversation.get_current_comment(conversation_statistics)
        comment_title = Conversation.get_comment_title(
            comment,
            current_comment,
            total_comments,
            tracker,
        )
        message = Comment.get_utter(metadata, comment_title)
        if type(message) is str:
            # No Button channel
            dispatcher.utter_message(message)
        else:
            dispatcher.utter_message(**message)

        return [
            SlotSet("number_voted_comments", current_comment),
            SlotSet("comment_text", comment_title),
            SlotSet("number_comments", total_comments),
            SlotSet("current_comment_id", comment.get("id")),
        ]

    def _dispatch_user_vote_on_all_comments(self, dispatcher):
        dispatcher.utter_message(template="utter_voted_all_comments")
        dispatcher.utter_message(template="utter_thanks_participation")
        # vote_form stop loop if vote slot is not None
        return [SlotSet("vote", "concordar")]


class ValidateVoteForm(FormValidationAction):
    """
    This action is called when the vote form is active.
    After ActionAskVote ran, action_listen is activated and user should input.
    This action validates what user typed

    return:
        dict with fields of the form values, in this case, only vote value.

    If the returned value is set to None, bot will again call ActionAskVote until a
    not null value is returned in this ValidateVoteForm action.
    With that, we mantain our user in a loop of this form until they want to quit OR
    all comments from the conversation are already voted on.

    The followed logic is:
        - If user value is one of : "Concordar", "Discordar, "Pular", 0, 1, 2
        a vote is computed
        - If user value is PARAR, it exists from the loop
        - If user value is not any of these, it is considered as a new comment, that is sent to EJ

    https://rasa.com/docs/rasa/forms/#validating-form-input
    """

    def name(self) -> Text:
        return "validate_vote_form"

    def validate_comment_confirmation(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:

        # TODO: improves NLU stories to deal with this path, instead of controlling it
        # in this method.
        comment_confirmation_value = tracker.get_slot("comment_confirmation")
        if comment_confirmation_value == "não":
            dispatcher.utter_message(template="utter_go_back_to_voting")
            return Comment.resume_voting(slot_value)

    def validate_comment(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:

        token = tracker.get_slot("ej_user_token")
        comment_text = tracker.latest_message["text"]
        conversation_id = tracker.get_slot("conversation_id_cache")
        comment = Comment(conversation_id, comment_text, token)
        try:
            comment.create()
            dispatcher.utter_message(template="utter_sent_comment")
            return Comment.resume_voting(slot_value)
        except:
            dispatcher.utter_message(template="utter_send_comment_error")

    def validate_vote(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate vote value."""

        if Conversation.user_wants_to_stop_participation(slot_value):
            custom_logger(f"Stoping voting because of slot_value {slot_value}")
            return Vote.stop_voting()
        # conversation_id_cache is necessary because add_new_comment intent can have numbers and
        # trigger auto_fill for conversation_id. Using conversation_id_cache we avoid this loosing the original ID.
        # https://github.com/RasaHQ/rasa/issues/5561
        conversation_id = tracker.get_slot("conversation_id_cache")
        conversation_text = tracker.get_slot("conversation_text")
        token = tracker.get_slot("ej_user_token")
        conversation = Conversation(conversation_id, conversation_text, token)
        custom_logger(f"Conversation object: {conversation}")
        statistics = conversation.get_participant_statistics()
        vote = Vote(slot_value, tracker)
        if vote.is_valid():
            custom_logger(f"POST vote to EJ API: {vote}")
            vote_data = vote.create(tracker.get_slot("current_comment_id"))
            self._dispatch_save_participant_vote(dispatcher, vote_data)

        if Conversation.time_to_ask_to_add_comment(statistics):
            custom_logger(
                f"TIME TO ASK COMMENT {Comment.pause_to_ask_comment(slot_value)}"
            )
            return Comment.pause_to_ask_comment(slot_value)

        if vote.is_valid():
            custom_logger(f"Dispatching conversation next comment")
            return self._dispatch_show_next_comment(dispatcher, statistics, vote)
        dispatcher.utter_message(template="utter_out_of_context")

    def _dispatch_save_participant_vote(self, dispatcher, vote_data):
        if vote_data.get("created"):
            dispatcher.utter_message(template="utter_vote_received")

    def _dispatch_show_next_comment(self, dispatcher, statistics, voting_helper):
        if not Conversation.no_comments_left_to_vote(statistics):
            return Vote.continue_voting()
        else:
            dispatcher.utter_message(template="utter_voted_all_comments")
            dispatcher.utter_message(template="utter_thanks_participation")
            return voting_helper.finished_voting()

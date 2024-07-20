from typing import Any, Dict, List, Text

from actions.logger import custom_logger
from rasa_sdk import Action, FormValidationAction, Tracker
from rasa_sdk.events import EventType, FollowupAction, SlotSet
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict

from ej.constants import EJCommunicationError
from ej.comment import Comment, CommentDialogue
from ej.conversation import Conversation
from ej.vote import Vote, VoteDialogue


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
        anonymous_votes_limit = int(tracker.get_slot("anonymous_votes_limit"))
        participant_can_add_comments = tracker.get_slot("participant_can_add_comments")
        conversation = Conversation(
            conversation_id,
            conversation_text,
            anonymous_votes_limit,
            participant_can_add_comments,
            tracker,
        )
        conversation_statistics = conversation.get_participant_statistics()
        if Conversation.no_comments_left_to_vote(conversation_statistics):
            return self._dispatch_user_vote_on_all_comments(dispatcher)

        has_completed_registration = tracker.get_slot("has_completed_registration")
        if Conversation.user_should_authenticate(
            has_completed_registration, anonymous_votes_limit, conversation_statistics
        ):
            return self._dispatch_start_authentication_flow(dispatcher)

        try:
            comment = conversation.get_next_comment()
            return self._dispatch_comment_to_vote(
                dispatcher, tracker, conversation_statistics, comment
            )
        except EJCommunicationError:
            return self._dispatch_errors(dispatcher)

    def _dispatch_errors(self, dispatcher):
        dispatcher.utter_message(template="utter_ej_communication_error")
        dispatcher.utter_message(template="utter_error_try_again_later")
        return [FollowupAction("action_session_start")]

    def _dispatch_start_authentication_flow(self, dispatcher):
        dispatcher.utter_message(template="utter_vote_limit_anonymous_reached")
        return [
            SlotSet("vote", "-"),
            SlotSet("comment_confirmation", "-"),
            SlotSet("comment", "-"),
            FollowupAction("authentication_form"),
        ]

    def _dispatch_comment_to_vote(
        self, dispatcher, tracker, conversation_statistics, next_comment
    ) -> List:
        total_comments = Conversation.get_total_comments(conversation_statistics)
        user_voted_comments = Conversation.get_user_voted_comments_counter(
            conversation_statistics
        )
        comment_title = Conversation.get_comment_title(
            next_comment,
            user_voted_comments,
            total_comments,
        )
        metadata = tracker.latest_message.get("metadata")
        message = CommentDialogue.get_utter(metadata, comment_title)
        if type(message) is str:
            dispatcher.utter_message(message)
        else:
            dispatcher.utter_message(**message)

        return [
            SlotSet("user_voted_comments", user_voted_comments),
            SlotSet("comment_text", comment_title),
            SlotSet("number_comments", total_comments),
            SlotSet("current_comment_id", next_comment.get("id")),
        ]

    def _dispatch_user_vote_on_all_comments(self, dispatcher):
        dispatcher.utter_message(template="utter_voted_all_comments")
        dispatcher.utter_message(template="utter_thanks_participation")
        return [SlotSet("vote", "concordar")]


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

    def validate_comment_confirmation(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:

        if CommentDialogue.user_refuses_to_add_comment(slot_value):
            dispatcher.utter_message(template="utter_go_back_to_voting")
            return CommentDialogue.resume_voting(slot_value)

    def validate_comment(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:

        user_comment = slot_value
        if not user_comment:
            return {}

        if Conversation.user_requested_new_conversation(user_comment):
            return CommentDialogue.resume_voting("")

        conversation_id = tracker.get_slot("conversation_id_cache")
        comment = Comment(conversation_id, user_comment, tracker)
        try:
            comment.create()
            dispatcher.utter_message(template="utter_sent_comment")
            return CommentDialogue.resume_voting(slot_value)
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

        if not slot_value:
            return {}

        conversation_id = tracker.get_slot("conversation_id_cache")
        conversation_text = tracker.get_slot("conversation_text")
        anonymous_votes_limit = tracker.get_slot("anonymous_votes_limit")
        participant_can_add_comments = tracker.get_slot("participant_can_add_comments")
        conversation = Conversation(
            conversation_id,
            conversation_text,
            anonymous_votes_limit,
            participant_can_add_comments,
            tracker,
        )
        statistics = conversation.get_participant_statistics()
        vote = Vote(slot_value, tracker)

        if Conversation.user_requested_new_conversation(slot_value):
            finished_voting_slots = VoteDialogue.finish_voting()
            dialogue_restart_slots = Conversation.restart_dialogue(slot_value)
            return {**finished_voting_slots, **dialogue_restart_slots}

        if vote.is_valid():
            custom_logger(f"POST vote to EJ API: {vote}")
            vote_data = vote.create(tracker.get_slot("current_comment_id"))
            self._dispatch_save_participant_vote(dispatcher, vote_data)
        else:
            if vote.is_internal():
                return self._dispatch_show_next_comment(
                    dispatcher, statistics, vote, tracker
                )
            dispatcher.utter_message(template="utter_invalid_vote_during_participation")
            return VoteDialogue.continue_voting(tracker)

        if Conversation.user_can_add_comment(statistics, tracker):
            custom_logger(
                f"TIME TO ASK COMMENT {CommentDialogue.ask_user_to_comment(slot_value)}"
            )
            return CommentDialogue.ask_user_to_comment(slot_value)

        if vote.is_valid():
            return self._dispatch_show_next_comment(
                dispatcher, statistics, vote, tracker
            )

    def _dispatch_save_participant_vote(self, dispatcher, vote_data):
        if vote_data.get("created"):
            dispatcher.utter_message(template="utter_vote_received")

    def _dispatch_show_next_comment(
        self, dispatcher, statistics, vote: Vote, tracker: Tracker
    ):
        if not Conversation.no_comments_left_to_vote(statistics):
            return VoteDialogue.continue_voting(tracker)
        else:
            dispatcher.utter_message(template="utter_voted_all_comments")
            dispatcher.utter_message(template="utter_thanks_participation")
            return Vote.finish_voting()

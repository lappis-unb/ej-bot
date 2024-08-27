from dataclasses import dataclass, field
from actions.checkers.api_error_checker import EJApiErrorManager
from ej.constants import EJCommunicationError
from ej.comment import CommentDialogue
from ej.conversation import Conversation
from ej.profile import Profile
from rasa_sdk.events import FollowupAction, SlotSet
from typing import Any, List
from actions.logger import custom_logger


@dataclass
class CheckSlotsInterface:
    """
    Defines a common interface to verify an action slots.
    """

    tracker: Any = None
    dispatcher: Any = None
    conversation: Any = None
    conversation_statistics: Any = None
    slots: List[Any] = field(default_factory=list)

    def should_return_slots_to_rasa(self) -> bool:
        """
        Returns True if the dialogue slots has to be updated.
        If True, the slots field must be updated with the corresponding SlotSet or FollowupAction.
        """
        raise Exception("not implemented")


@dataclass
class CheckNextCommentSlots(CheckSlotsInterface):
    """
    Request to EJ API the next comment to vote and update the user statistics slots.
    """

    def should_return_slots_to_rasa(self) -> bool:
        try:
            comment = self.conversation.get_next_comment()
            self.set_slots(comment)
        except EJCommunicationError:
            ej_api_error_manager = EJApiErrorManager()
            self.slots = ej_api_error_manager.get_slots()
        return True

    def _dispatch_messages(
        self, comment, user_voted_comments, conversation_total_comments
    ):
        comment_content = comment["content"]
        metadata = self.tracker.latest_message.get("metadata")
        message = CommentDialogue.get_utter_message(
            metadata, comment_content, user_voted_comments, conversation_total_comments
        )
        if type(message) is str:
            self.dispatcher.utter_message(message)
        else:
            self.dispatcher.utter_message(**message)

    def set_slots(self, comment):
        conversation_total_comments = Conversation.get_total_comments(
            self.conversation_statistics
        )
        user_voted_comments = Conversation.get_user_voted_comments_counter(
            self.conversation_statistics
        )

        self._dispatch_messages(
            comment, user_voted_comments, conversation_total_comments
        )
        self.slots = [
            SlotSet("user_voted_comments", user_voted_comments),
            SlotSet("comment_content", comment["content"]),
            SlotSet("number_comments", conversation_total_comments),
            SlotSet("current_comment_id", comment.get("id")),
        ]


class CheckNeedToAskAboutProfile(CheckSlotsInterface):
    """
    Verify if the user needs to answer profile questions.
    """

    def should_return_slots_to_rasa(self) -> bool:
        try:
            profile = Profile(self.tracker)
        except EJCommunicationError:
            ej_api_error_manager = EJApiErrorManager()
            self.slots = ej_api_error_manager.get_slots()
            return True
        response, next = profile.need_to_ask_about_profile(
            self.conversation, self.conversation_statistics, self.tracker
        )
        if response:
            self._dispatch_messages(profile)
            self.set_slots(next=next)
            return True
        return False

    def _dispatch_messages(self, profile: Profile):
        if len(profile.remaining_questions) == len(profile.questions):
            self.dispatcher.utter_message(response="utter_profile_intro")

    def set_slots(self, next):
        self.slots = [
            SlotSet("vote", "-"),
            SlotSet("comment_confirmation", "-"),
            SlotSet("comment", "-"),
            SlotSet("need_to_ask_profile_question", True),
            SlotSet("next_count_to_send_profile_question", str(next)),
            SlotSet("profile_question", None),
            FollowupAction("profile_form"),
        ]


@dataclass
class CheckExternalAutenticationSlots(CheckSlotsInterface):
    """
    Test if the user has reached the anonymous vote limit and needs to authenticate.
    """

    def should_return_slots_to_rasa(self) -> bool:
        has_completed_registration = self.tracker.get_slot("has_completed_registration")
        anonymous_votes_limit = int(self.tracker.get_slot("anonymous_votes_limit"))
        if Conversation.user_should_authenticate(
            has_completed_registration,
            anonymous_votes_limit,
            self.conversation_statistics,
        ):
            self._dispatch_messages()
            self.set_slots()
            return True
        return False

    def _dispatch_messages(self):
        self.dispatcher.utter_message(template="utter_vote_limit_anonymous_reached")

    def set_slots(self):
        self.slots = [
            SlotSet("vote", "-"),
            SlotSet("comment_confirmation", "-"),
            SlotSet("comment", "-"),
            FollowupAction("authentication_form"),
        ]


@dataclass
class CheckEndConversationSlots(CheckSlotsInterface):
    """
    Test if the user has voted in all available comments.
    """

    def should_return_slots_to_rasa(self):
        if not Conversation.available_comments_to_vote(self.conversation_statistics):
            self._dispatch_messages()
            self.set_slots()
            return True
        return False

    def _dispatch_messages(self):
        self.dispatcher.utter_message(template="utter_voted_all_comments")
        self.dispatcher.utter_message(template="utter_thanks_participation")

    def set_slots(self):
        self.slots = [SlotSet("vote", "concordar")]

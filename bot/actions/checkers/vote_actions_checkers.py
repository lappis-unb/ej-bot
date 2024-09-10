from dataclasses import dataclass

from actions.checkers.api_error_checker import EJClientErrorManager
from actions.checkers.profile_actions_checkers import CheckSlotsInterface
from ej.comment import CommentDialogue
from ej.conversation import Conversation
from ej.profile import Profile
from ej.settings import EJCommunicationError
from ej.vote import SlotsType, VoteDialogue
from rasa_sdk.events import SlotSet


@dataclass
class CheckRemainingCommentsSlots(CheckSlotsInterface):
    """
    Check if after a vote, still exists an next comment to vote.
    """

    def has_slots_to_return(self) -> bool:
        available_comments_exists = Conversation.available_comments_to_vote(
            self.conversation_statistics
        )
        self.set_slots(available_comments_exists)
        return True

    def set_slots(self, available_comments_exists=True):
        if available_comments_exists:
            if Conversation.get_voted_comments(self.conversation_statistics):
                self.dispatcher.utter_message(response="utter_vote_received")
            self.slots = VoteDialogue.restart_vote_form_slots()
        else:
            self.dispatcher.utter_message(response="utter_thanks_participation")
            self.slots = VoteDialogue.completed_vote_form_slots(self.slots_type)


@dataclass
class CheckNextCommentSlots(CheckSlotsInterface):
    """
    Request to EJ API the next comment to vote and update the user statistics slots.
    """

    def has_slots_to_return(self) -> bool:
        try:
            comment = self.conversation.get_next_comment()
            if comment:
                self.set_slots(comment)
            else:
                self.dispatcher.utter_message(response="utter_thanks_participation")
                self.slots = VoteDialogue.completed_vote_form_slots(SlotsType.LIST)
        except EJCommunicationError:
            ej_client_error_manager = EJClientErrorManager()
            self.slots = ej_client_error_manager.get_slots()
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
        user_voted_comments = Conversation.get_voted_comments(
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

    def has_slots_to_return(self) -> bool:
        try:
            profile = Profile(self.tracker)
        except EJCommunicationError:
            ej_client_error_manager = EJClientErrorManager()
            self.slots = ej_client_error_manager.get_slots()
            return True
        response, next = profile.need_to_ask_about_profile(
            self.conversation, self.conversation_statistics, self.tracker
        )
        if response:
            self.set_slots(next=next)
            return True
        return False

    def set_slots(self, next):
        match self.slots_type:
            case SlotsType.LIST:
                self.slots = [
                    SlotSet("vote", "-"),
                    SlotSet("need_to_ask_profile_question", True),
                    SlotSet("next_count_to_send_profile_question", str(next)),
                    SlotSet("profile_question", None),
                ]
            case SlotsType.DICT:
                self.slots = {
                    "vote": "-",
                    "need_to_ask_profile_question": True,
                    "next_count_to_send_profile_question": str(next),
                    "profile_question": None,
                }


@dataclass
class CheckExternalAuthenticationSlots(CheckSlotsInterface):
    """
    Test if the user has reached the anonymous vote limit and needs to authenticate.
    """

    def has_slots_to_return(self) -> bool:
        has_completed_registration = self.tracker.get_slot("has_completed_registration")
        anonymous_votes_limit = int(self.tracker.get_slot("anonymous_votes_limit"))
        if Conversation.user_should_authenticate(
            has_completed_registration,
            anonymous_votes_limit,
            self.conversation_statistics,
        ):
            self.set_slots()
            return True
        return False

    def set_slots(self):
        match self.slots_type:
            case SlotsType.LIST:
                self.slots = [
                    SlotSet("vote", "-"),
                    SlotSet("ask_to_authenticate", True),
                ]
            case SlotsType.DICT:
                self.slots = {"vote": "-", "ask_to_authenticate": True}
            case _:
                raise Exception


@dataclass
class CheckUserCommentSlots(CheckSlotsInterface):
    """
    Test if the user has voted in all available comments.
    """

    def has_slots_to_return(self) -> bool:
        if not Conversation.available_comments_to_vote(self.conversation_statistics):
            self._dispatch_messages()
            self.set_slots()
            return True
        return False

    def _dispatch_messages(self):
        self.dispatcher.utter_message(response="utter_thanks_participation")

    def set_slots(self):
        self.slots = VoteDialogue.completed_vote_form_slots(self.slots_type)


@dataclass
class CheckUserCanAddCommentsSlots(CheckSlotsInterface):
    """
    Test if the user can add comments to the conversation.
    """

    def has_slots_to_return(self) -> bool:
        if Conversation.user_can_add_comment(
            self.conversation_statistics, self.tracker
        ):
            self.set_slots()
            return True
        return False

    def set_slots(self):
        self.slots = CommentDialogue.deactivate_vote_form(self.slot_value)

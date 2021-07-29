# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this gu"id"e on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions
import os
import logging
from typing import Text, List, Any, Dict
import json

from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FollowupAction, EventType
from rasa_sdk.types import DomainDict

from .ej_connector import API, EJCommunicationError
from .utils import *
from .helpers import VotingHelper, ConversationHelper

logger = logging.getLogger(__name__)


#
#
class ActionSetupConversation(Action):
    """
    Logs user in EJ and get their conversation statistic according to their account
    If user provides an phone number, it will be used to generate login token. If not,
    rasa conversation id will be used instead

    returns the following slots, filled:
        - user_token: generated when logging in EJ
        - number_comments: total number of comments in current conversation
        - number_voted_comments: number of comments that were already voted by current user
        - current_comment_id: id of the comment that will be displayed
        - comment_text: text content of the comment that will be displayed

    if any problem occurs during connection with EJ, conversation will be restarted
    """

    def name(self):
        return "action_setup_conversation"

    def run(self, dispatcher, tracker, domain):
        logger.debug("action ActionSetupConversation called")
        user_phone_number = tracker.get_slot("regex_phone_number")
        conversation_id = tracker.get_slot("conversation_id")
        try:
            last_intent = tracker.latest_message["intent"].get("name")
            user_info = authenticate_user(
                user_phone_number, last_intent, tracker.sender_id
            )
            user = user_info["user"]
            dispatcher.utter_message(template=user_info["utter_name"])

            statistics = API.get_user_conversation_statistics(
                conversation_id, user.token
            )
            first_comment = API.get_next_comment(conversation_id, user.token)
        except EJCommunicationError:
            dispatcher.utter_message(template="utter_ej_communication_error")
            dispatcher.utter_message(template="utter_error_try_again_later")
            return [FollowupAction("action_session_start")]

        if tracker.get_slot("current_channel_info") == "rocket_livechat":
            # explain how user can vote according to current channel
            dispatcher.utter_message(template="utter_explain_no_button_participation")
        else:
            dispatcher.utter_message(template="utter_explain_button_participation")

        statistics = API.get_user_conversation_statistics(conversation_id, user.token)
        first_comment = API.get_next_comment(conversation_id, user.token)
        return [
            SlotSet("number_voted_comments", statistics["votes"]),
            SlotSet(
                "number_comments", statistics["missing_votes"] + statistics["votes"]
            ),
            SlotSet("comment_text", first_comment["content"]),
            SlotSet("current_comment_id", first_comment["id"]),
            SlotSet("ej_user_token", user.token),
        ]


class ActionFollowUpForm(Action):
    def name(self):
        return "action_follow_up_form"

    def run(self, dispatcher, tracker, domain):
        logger.debug("action ActionFollowUpForm called")
        vote = tracker.get_slot("vote")

        if ConversationHelper.stop_participation(vote):
            dispatcher.utter_message(template="utter_thanks_participation")
            dispatcher.utter_message(template="utter_stopped")

        if ConversationHelper.pause_to_ask_phone_number(vote):
            return [
                SlotSet("vote", None),
                FollowupAction("utter_ask_phone_number_again"),
            ]
        if ConversationHelper.is_vote_on_new_conversation(vote):
            return [
                SlotSet("vote", None),
                FollowupAction("action_get_conversation_info"),
            ]

        return [
            SlotSet("vote", None),
            SlotSet("conversation_id", None),
        ]


class ActionAskVote(Action):
    """
    This action is called when the vote form is active.
    It shows a comment for user to vote on, and also their statistics in the conversation.

    If user is in a channel that can render buttons, "Concordar", "Discordar" and "Pular"
    buttons are displayed
    If not, user is instructed to vote use number (1,-1 and 0)

    if any problem occurs during connection with EJ, conversation will be restarted

    https://rasa.com/docs/rasa/forms/#using-a-custom-action-to-ask-for-the-next-slot
    """

    def name(self) -> Text:
        return "action_ask_vote"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:

        conversation_id = tracker.get_slot("conversation_id")
        token = tracker.get_slot("ej_user_token")
        conversation_helper = ConversationHelper(conversation_id, token)
        try:
            statistics = conversation_helper.get_participant_statistics()
            total_comments = conversation_helper.get_total_comments(statistics)
            voted_comments = conversation_helper.get_voted_comments(statistics)
            comment = conversation_helper.get_next_comment()
        except EJCommunicationError:
            return ConversationHelper.dispatch_errors(dispatcher, FollowupAction)

        comment_title = conversation_helper.get_comment_title(
            comment, voted_comments, total_comments
        )
        metadata = tracker.latest_message.get("metadata")
        message = get_comment_utter(metadata, comment_title)
        dispatcher.utter_message(**message)

        return [
            SlotSet("number_voted_comments", voted_comments),
            SlotSet("comment_text", comment_title),
            SlotSet("number_comments", total_comments),
            SlotSet("current_comment_id", comment.get("id")),
        ]


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
        - If user value is one of : "Concordar", "Discordar, "Pular", 0, 1, -1
        a vote is computed
        - If user value is PARAR, it exists from the loop
        - If user value is not any of these, it is considered as a new comment, that is sent to EJ

    https://rasa.com/docs/rasa/forms/#validating-form-input
    """

    def name(self) -> Text:
        return "validate_vote_form"

    def validate_vote(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate vote value."""
        logger.debug("form validator ValidateVoteForm called")
        token = tracker.get_slot("ej_user_token")
        conversation_id = tracker.get_slot("conversation_id")
        voting_helper = VotingHelper(slot_value, token)
        conversation_helper = ConversationHelper(conversation_id, token)

        # TODO: Check if already asked twice the phone number
        statistics = conversation_helper.get_participant_statistics()
        if conversation_helper.ask_phone_number_again(
            tracker.get_slot("regex_phone_number"), statistics
        ):
            return VotingHelper.pause_voting()

        if ConversationHelper.stop_participation(slot_value):
            return VotingHelper.stop_voting()

        current_intent = tracker.latest_message.get("intent").get("name")
        if ConversationHelper.intent_starts_new_conversation(current_intent):
            return ConversationHelper.starts_conversation_from_another_link()

        if voting_helper.vote_is_valid():
            comment_id = tracker.get_slot("current_comment_id")
            vote = voting_helper.new_vote(comment_id)
            if vote["created"]:
                dispatcher.utter_message(template="utter_vote_received")
            if conversation_helper.user_have_comments_to_vote():
                return VotingHelper.continue_voting()
            else:
                dispatcher.utter_message(template="utter_voted_all_comments")
                dispatcher.utter_message(template="utter_thanks_participation")
                return voting_helper.finished_voting()
        dispatcher.utter_message(template="utter_out_of_context")


class ActionGetConversationInfo(Action):
    """
    When in socketio channel:
        Send request to EJ with current URL where the bot is hosted
        Get conversation ID and Title in return

    When in other channels:
        Get already set slot conversation id and send it to EJ
        to get corresponding conversation title
    """

    def name(self):
        return "action_get_conversation_info"

    def run(self, dispatcher, tracker, domain):
        logger.debug("action ActionGetConversationInfo called")
        if tracker.get_latest_input_channel() == "socketio":
            bot_url = tracker.get_slot("url")
            try:
                conversation_info = API.get_conversation_info_by_url(bot_url)
            except EJCommunicationError:
                dispatcher.utter_message(template="utter_ej_communication_error")
                dispatcher.utter_message(template="utter_error_try_again_later")
                return [FollowupAction("action_session_start")]
            if conversation_info:
                # TODO: If a domain has more than one conversation, need to think how to deal with it
                conversation_text = conversation_info.get("conversation").get("text")
                conversation_id = conversation_info.get("conversation").get("id")

            else:
                dispatcher.utter_message(template="utter_ej_connection_doesnt_exist")
                dispatcher.utter_message(template="utter_error_try_again_later")
                return [FollowupAction("action_session_start")]
        else:
            conversation_id = tracker.get_slot("conversation_id")
            if conversation_id:
                conversation = API.get_conversation(conversation_id)
                conversation_text = conversation.get("text")
            else:
                dispatcher.utter_message(template="utter_no_selected_conversation")
                return [FollowupAction("action_session_start")]

        return [
            SlotSet("conversation_text", conversation_text),
            SlotSet("conversation_id", conversation_id),
        ]


class ActionSetChannelInfo(Action):
    """
    Rasa set current user channel on tracker.get_latest_input_channel()
    but it cannot read nuances such as:
        - Being on a private or group chat on telegram or rocketchat
        - Being on rocketchat livechat or any other kind of chat

    This kind of data is set on message metadata, and we access it to
    set current channel with more detail
    """

    def name(self):
        return "action_set_channel_info"

    def run(self, dispatcher, tracker, domain):
        logger.debug("action ActionSetChannelInfo called")
        channel = tracker.get_latest_input_channel()

        if tracker.get_latest_input_channel() == "rocketchat":
            if "agent" in tracker.latest_message["metadata"]:
                channel = "rocket_livechat"
        if tracker.get_latest_input_channel() == "telegram":
            bot_telegram_username = os.getenv("TELEGRAM_BOT_NAME")
            return [
                SlotSet("current_channel_info", channel),
                SlotSet("bot_telegram_username", bot_telegram_username),
            ]
        return [
            FollowupAction("action_get_conversation_info"),
            SlotSet("current_channel_info", channel),
        ]


class ActionSetConversationSlots(Action):
    """
    This action is called when the user whants to creates a participation link.
    After start_group_interaction itent, this action is called.

    return:
        conversation_text and conversation_id slots
    """

    def name(self):
        return "action_set_conversation_slots"

    def run(self, dispatcher, tracker, domain):
        logger.debug("action ActionSetConversationSlots called")
        conversation_id = tracker.get_slot("conversation_id")
        conversation_text = ""
        if conversation_id:
            conversation = API.get_conversation(conversation_id)
            conversation_text = conversation.get("text")
        return [
            SlotSet("conversation_text", conversation_text),
            SlotSet("conversation_id", conversation_id),
        ]


class ActionGetConversationList(Action):
    """
    This action is called when the user wants to see all the available conversations.
    It shows the ID and the Title of the conversation.
    """

    def name(self):
        return "action_get_conversations"

    def run(self, dispatcher, tracker, domain):
        logger.debug("action ActionGetConversations called")
        if tracker.get_latest_input_channel() == "telegram":
            try:
                conversations = API.get_conversations()
                if conversations["count"] == 0:
                    dispatcher.utter_message(template="utter_no_conversations")
                else:
                    dispatcher.utter_message(template="utter_show_conversations")
                    dispatcher.utter_message(template="utter_explain_id_conversation")
                    ids = [result["id"] for result in conversations["results"]]
                    texts = [result["text"] for result in conversations["results"]]
                    result = "\n".join(
                        f"Identificador da conversa - {str(ids[i])}\nTítulo da conversa - {text}\n  "
                        for i, text in enumerate(texts)
                    )

                    dispatcher.utter_message(text=result)
            except EJCommunicationError:
                dispatcher.utter_message(template="utter_ej_communication_error")
                dispatcher.utter_message(template="utter_error_try_again_later")
                return [FollowupAction("action_session_start")]

        return []

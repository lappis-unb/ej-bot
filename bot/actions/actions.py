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
from .ej_connector.user import User
from .ej_connector.constants import MENSSAGE_CHANNELS
from .utils import *
from .ej_connector.helpers import VotingHelper, EngageFactory
from .ej_connector.conversation import ConversationController

logger = logging.getLogger(__name__)


class ActionSetupConversation(Action):
    """
    Logs user in EJ and get their conversation statistic according to their account
    If user provides a phone number, it will be used to generate login token. If not,
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
        self.response = []
        if ConversationController.is_valid(tracker):
            try:
                user_phone_number = tracker.get_slot("regex_phone_number")
                user = User(tracker.sender_id, phone_number=user_phone_number)
                last_intent = tracker.latest_message["intent"].get("name")
                user.authenticate(last_intent)
                conversation_controller = ConversationController(tracker, user.token)
                self.dispatch_user_authentication(user, dispatcher)
                self.set_response_to_participation(conversation_controller, user)
                self.dispatch_explain_participation(
                    tracker.get_slot("current_channel_info"), dispatcher
                )
            except EJCommunicationError:
                return self.dispatch_communication_error_with_ej(dispatcher)
        return self.response

    def dispatch_user_authentication(self, user, dispatcher):
        dispatcher.utter_message(template=user.authenticate_utter)

    def dispatch_communication_error_with_ej(self, dispatcher):
        dispatcher.utter_message(template="utter_ej_communication_error")
        dispatcher.utter_message(template="utter_error_try_again_later")
        return [FollowupAction("action_session_start")]

    def dispatch_explain_participation(self, channel_info_slot, dispatcher):
        if channel_info_slot == "rocket_livechat" or channel_info_slot == "twilio":
            # explain how user can vote according to current channel
            dispatcher.utter_message(template="utter_explain_no_button_participation")
        else:
            dispatcher.utter_message(template="utter_explain_button_participation")

    def set_response_to_participation(self, conversation_controller, user):
        statistics = conversation_controller.api.get_participant_statistics()
        first_comment = conversation_controller.api.get_next_comment()
        self.response = [
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
        self.response = []

        self.dispatch_if_stop_participation(dispatcher, vote)
        self.set_response_to_ask_phone_number_again(vote)
        self.set_response_to_starts_new_conversation(vote)
        self.set_response_to_continue_conversation(vote)
        return self.response

    def dispatch_if_stop_participation(self, dispatcher, vote):
        if ConversationController.user_wants_to_stop_participation(vote):
            dispatcher.utter_message(template="utter_thanks_participation")
            dispatcher.utter_message(template="utter_stopped")

    def set_response_to_ask_phone_number_again(self, vote):
        if ConversationController.pause_to_ask_phone_number(vote):
            self.response = [
                SlotSet("vote", None),
                FollowupAction("action_check_if_user_has_phone_number"),
            ]

    def set_response_to_starts_new_conversation(self, vote):
        if ConversationController.is_vote_on_new_conversation(vote):
            self.response = [
                SlotSet("vote", None),
                FollowupAction("action_get_conversation_info"),
            ]

    def set_response_to_continue_conversation(self, vote):
        if not self.response and vote == None:
            self.response = [
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

        conversation_controller = ConversationController(tracker)
        self.response = []
        channel = tracker.get_latest_input_channel()
        if not conversation_controller.user_have_comments_to_vote():
            return self.dispatch_user_vote_on_all_comments(dispatcher)
        try:
            metadata = tracker.latest_message.get("metadata")
            self.set_response_to_next_comment(
                dispatcher, metadata, conversation_controller, channel
            )
        except EJCommunicationError:
            return ConversationController.dispatch_errors(dispatcher, FollowupAction)

        return self.response

    def set_response_to_next_comment(
        self, dispatcher, metadata, conversation_controller, channel
    ):
        statistics = conversation_controller.api.get_participant_statistics()
        total_comments = conversation_controller.api.get_total_comments(statistics)
        current_comment = conversation_controller.api.get_current_comment(statistics)
        comment = conversation_controller.api.get_next_comment()
        comment_title = conversation_controller.api.get_comment_title(
            comment, current_comment, total_comments
        )

        message = get_comment_utter(metadata, comment_title, channel)

        if type(message) is str:
            # No Button channel
            dispatcher.utter_message(message)
        else:
            dispatcher.utter_message(**message)

        self.response = [
            SlotSet("number_voted_comments", current_comment),
            SlotSet("comment_text", comment_title),
            SlotSet("number_comments", total_comments),
            SlotSet("current_comment_id", comment.get("id")),
        ]

    def dispatch_user_vote_on_all_comments(self, dispatcher):
        dispatcher.utter_message(template="utter_voted_all_comments")
        dispatcher.utter_message(template="utter_thanks_participation")
        # vote_form stop loop if vote slot is not None
        return [SlotSet("vote", "concordar")]


class ActionCheckPhoneNumber(Action):
    def name(self) -> Text:
        return "action_check_if_user_has_phone_number"

    def run(self, dispatcher, tracker, domain):
        logger.debug("action check phone number in profile called")
        phone_number = API.get_profile(tracker.get_slot("ej_user_token"))

        if phone_number:
            return [
                SlotSet("regex_phone_number", phone_number),
                FollowupAction("vote_form"),
            ]
        else:
            return [FollowupAction("utter_ask_phone_number_again")]


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

        # dispatcher.utter_message(text=channel)
        if ConversationController.user_wants_to_stop_participation(slot_value):
            return VotingHelper.stop_voting()
        voting_helper = VotingHelper(slot_value, tracker)
        conversation_controller = ConversationController(tracker)
        self.dispatch_save_participant_vote(tracker, dispatcher, voting_helper)
        self.dispatch_save_participant_comment(
            dispatcher, voting_helper, conversation_controller
        )
        self.dispatch_invite_to_join_group(tracker, dispatcher, conversation_controller)
        if conversation_controller.time_to_ask_phone_number_again():
            return VotingHelper.pause_voting_to_ask_phone_number()
        if conversation_controller.intent_starts_new_conversation():
            return ConversationController.starts_conversation_from_another_link()
        if voting_helper.vote_is_valid() or voting_helper.user_enters_a_new_comment():
            return self.dispatch_show_next_comment(
                dispatcher, conversation_controller, voting_helper
            )
        dispatcher.utter_message(template="utter_out_of_context")

    def dispatch_save_participant_comment(
        self, dispatcher, voting_helper, conversation_controller
    ):
        if voting_helper.user_enters_a_new_comment():
            try:
                voting_helper.send_new_comment(conversation_controller.conversation_id)
                dispatcher.utter_message(template="utter_sent_comment")
            except Exception:
                dispatcher.utter_message(template="utter_send_comment_error")

    def dispatch_save_participant_vote(self, tracker, dispatcher, voting_helper):
        if voting_helper.vote_is_valid():
            vote = voting_helper.new_vote(tracker.get_slot("current_comment_id"))
            if vote["created"]:
                dispatcher.utter_message(template="utter_vote_received")

    def dispatch_show_next_comment(
        self, dispatcher, conversation_controller, voting_helper
    ):
        if conversation_controller.user_have_comments_to_vote():
            return VotingHelper.continue_voting()
        else:
            dispatcher.utter_message(template="utter_voted_all_comments")
            dispatcher.utter_message(template="utter_thanks_participation")
            return voting_helper.finished_voting()

    def dispatch_invite_to_join_group(
        self, tracker, dispatcher, conversation_controller
    ):
        bot_name = tracker.get_slot("bot_telegram_username")
        telegram_engagement_group = tracker.get_slot("telegram_engagement_group")
        statistics = conversation_controller.api.get_participant_statistics()
        if conversation_controller.time_to_invite_to_engage(
            statistics, bot_name, telegram_engagement_group
        ):
            dispatcher.utter_message(
                template="utter_invite_user_to_join_group",
                telegram_engagement_group=EngageFactory.bot_has_engage_link(bot_name),
            )


# TODO: Rename to ActionGetConversation
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
        if tracker.get_latest_input_channel() == "twilio":
            bot_whatsapp_number = os.getenv("TWILIO_WHATSAPP")

            return [
                SlotSet("current_channel_info", channel),
                SlotSet("bot_whatsapp_number", number_from_wpp(bot_whatsapp_number)),
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
        if tracker.get_latest_input_channel() in MENSSAGE_CHANNELS.values():

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

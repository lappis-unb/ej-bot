from dataclasses import dataclass
import logging
import re

from ej.ej_api import EjApi
from ej.comment import CommentDialogue
from actions.logger import custom_logger
from rasa_sdk import Tracker

from .constants import EJCommunicationError, START_CONVERSATION_COMMAND
from .routes import (
    conversation_random_comment_url,
    conversation_url,
    user_statistics_url,
)


logger = logging.getLogger(__name__)


@dataclass
class Conversation:
    """Conversation controls requests to EJ API and some validations during bot execution."""

    def __init__(
        self,
        conversation_id,
        conversation_title: str,
        anonymous_votes_limit: int,
        participant_can_add_comments: bool,
        tracker: Tracker,
    ):
        self.id = conversation_id
        self.title = conversation_title
        self.participant_can_add_comments = participant_can_add_comments
        self.anonymous_votes_limit = anonymous_votes_limit
        self.ej_api = EjApi(tracker)

    @staticmethod
    def get_by_id(conversation_id, tracker: Tracker):
        ej_api = EjApi(tracker)
        try:
            response = ej_api.request(conversation_url(conversation_id))
            conversation = response.json()
            if len(conversation) == 0:
                raise EJCommunicationError
            return conversation
        except:
            raise EJCommunicationError

    @staticmethod
    def user_requested_new_conversation(user_input: str):
        """
        return true if user_input is equal to "/START_CONVERSATION_COMMAND ID".
        """
        pattern = re.compile(f"^{START_CONVERSATION_COMMAND}\s\d+")
        return re.search(pattern, user_input)

    @staticmethod
    def restart_dialogue(user_channel_input: str):
        """
        check if user_channel_input is a request to participate on a new conversation.
        If so, returns a dictionary with updated NLU slots.
        """
        # user_channel_input must be /start <id>
        conversation_id = user_channel_input.split(" ")[1]
        return {
            "restart_conversation": True,
            "conversation_id_cache": conversation_id,
            "conversation_id": conversation_id,
        }

    def get_participant_statistics(self):
        try:
            url = user_statistics_url(self.id)
            response = self.ej_api.request(url)
            response = response.json()
        except:
            raise EJCommunicationError
        return response

    def get_next_comment(self):
        url = conversation_random_comment_url(self.id)
        try:
            response = self.ej_api.request(url)
            comment = response.json()
            comment_url_as_list = comment["links"]["self"].split("/")
            comment["id"] = comment_url_as_list[len(comment_url_as_list) - 2]
            return comment
        except Exception as e:
            raise EJCommunicationError

    @staticmethod
    def user_should_authenticate(
        has_completed_registration: bool, anonymous_votes_limit: int, statistics
    ):
        if not has_completed_registration:
            custom_logger(f"ENTROU NA VALIDAÇÃO DE AUTENTICAÇÃO")
            comments_counter = Conversation.get_user_voted_comments_counter(statistics)
            if comments_counter == anonymous_votes_limit:
                return True
        return False

    @staticmethod
    def no_comments_left_to_vote(statistics):
        return statistics["missing_votes"] == 0

    @staticmethod
    def get_total_comments(statistics):
        return statistics["total_comments"]

    @staticmethod
    def get_user_voted_comments_counter(statistics):
        return statistics["comments"]


    @staticmethod
    def user_can_add_comment(statistics, tracker: Tracker) -> bool:
        participant_can_add_comments = tracker.get_slot("participant_can_add_comments")
        if not participant_can_add_comments:
            return False
        total_comments = Conversation.get_total_comments(statistics)
        current_comment = Conversation.get_user_voted_comments_counter(statistics)
        return (total_comments >= 4 and current_comment == 4) or (
            total_comments < 4 and current_comment == 2
        )
        return False

    @staticmethod
    def pause_to_ask_comment(vote_slot_value):
        return str(vote_slot_value).upper() == "PAUSA PARA PEDIR COMENTARIO"

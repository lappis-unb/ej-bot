import logging
import re

from actions.ej_connector.ej_api import EjApi
from rasa_sdk import Tracker

from .constants import EJCommunicationError, START_CONVERSATION_COMMAND
from .routes import (
    conversation_random_comment_url,
    conversation_url,
    user_statistics_url,
    webchat_domain_url,
)


logger = logging.getLogger(__name__)


class Conversation:
    """Conversation controls requests to EJ API and some validations during bot execution."""

    def __init__(self, conversation_id, conversation_title: str, tracker: Tracker):
        self.id = conversation_id
        self.title = conversation_title
        self.ej_api = EjApi(tracker)

    @staticmethod
    def get_by_bot_url(url):
        ej_api = EjApi(tracker=None)
        try:
            response = ej_api.request(webchat_domain_url(url))
            return response.json()
        except:
            raise EJCommunicationError

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
        check if user_channel_input is a request to participant on a new conversation.
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
    def no_comments_left_to_vote(statistics):
        return statistics["missing_votes"] == 0

    @staticmethod
    def get_total_comments(statistics):
        return statistics["total_comments"]

    @staticmethod
    def get_user_voted_comments_counter(statistics):
        return statistics["comments"]

    @staticmethod
    def get_comment_title(comment, user_voted_comments, total_comments):
        return f"*{comment['content']}* \n O que você acha disso ({user_voted_comments}/{total_comments})?"

    @staticmethod
    def user_wants_to_stop_participation(vote_slot_value):
        return str(vote_slot_value).upper() == "PARAR"

    @staticmethod
    def time_to_ask_to_add_comment(statistics, tracker: Tracker) -> bool:
        comment_confirmation = tracker.get_slot("comment_confirmation")
        if not comment_confirmation:
            total_comments = Conversation.get_total_comments(statistics)
            current_comment = Conversation.get_user_voted_comments_counter(statistics)
            return (total_comments >= 4 and current_comment == 4) or (
                total_comments < 4 and current_comment == 2
            )
        return False

    @staticmethod
    def starts_conversation_from_another_link():
        """
        Rasa end a form when all slots are filled. This method
        fill vote slot with "novo link de participação" value, forcing the form to stop.
        On ActionFollowUpForm class, whe check if vote is == novo link de participação, if so,
        we restart the story with the new conversation_id.

        This is necessary on the cenario where user is participating on a conversation,
        not vote on all comments, and then click on a new participation link. We need to
        stop the form, restarting the story from the begining.
        """
        return {"vote": "novo link de participação"}

    @staticmethod
    def pause_to_ask_comment(vote_slot_value):
        return str(vote_slot_value).upper() == "PAUSA PARA PEDIR COMENTARIO"

    @staticmethod
    def is_vote_on_new_conversation(vote_slot_value):
        return vote_slot_value == "novo link de participação"

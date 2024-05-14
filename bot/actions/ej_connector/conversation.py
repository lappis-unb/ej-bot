import logging
import requests

from .constants import EJCommunicationError
from .routes import (
    webchat_domain_url,
    user_statistics_url,
    auth_headers,
    HEADERS,
    conversation_random_comment_url,
    conversation_url,
)


logger = logging.getLogger(__name__)


class Conversation:
    """Conversation controls requests to EJ API and some validations during bot execution."""

    def __init__(self, conversation_id, conversation_title, token=None):
        self.id = conversation_id
        self.title = conversation_title
        self.token = token

    @staticmethod
    def get_by_bot_url(url):
        try:
            response = requests.get(webchat_domain_url(url), headers=HEADERS)
            response = response.json()
        except:
            raise EJCommunicationError
        return response

    @staticmethod
    def get_by_id(conversation_id):
        try:
            response = requests.get(conversation_url(conversation_id), headers=HEADERS)
            conversation = response.json()
            if len(conversation) == 0:
                raise EJCommunicationError
            return conversation
        except:
            raise EJCommunicationError

    def get_participant_statistics(self):
        try:
            url = user_statistics_url(self.id)
            response = requests.get(url, headers=auth_headers(self.token))
            response = response.json()
        except:
            raise EJCommunicationError
        return response

    def get_next_comment(self):
        url = conversation_random_comment_url(self.id)
        try:
            response = requests.get(url, headers=auth_headers(self.token))
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
    def get_current_comment(statistics):
        return statistics["comments"]

    @staticmethod
    def get_comment_title(comment_content, current_comment, total_comments, tracker):
        if tracker.get_latest_input_channel() == "twilio":
            return f"{'*'+comment_content['content']+'*'} \n O que você acha disso ({current_comment}/{total_comments})?"
        return f"{comment_content['content']} \n O que você acha disso ({current_comment}/{total_comments})?"

    @staticmethod
    def user_wants_to_stop_participation(vote_slot_value):
        return str(vote_slot_value).upper() == "PARAR"

    @staticmethod
    def time_to_ask_to_add_comment(statistics):
        total_comments = Conversation.get_total_comments(statistics)
        current_comment = Conversation.get_current_comment(statistics)
        return (total_comments >= 4 and current_comment == 4) or (
            total_comments < 4 and current_comment == 2
        )

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

from dataclasses import dataclass
import logging

from ej.ej_api import EjApi
from rasa_sdk import Tracker

from .constants import EJCommunicationError
from .routes import (
    conversation_random_comment_url,
    conversation_url,
    user_statistics_url,
)


logger = logging.getLogger(__name__)


@dataclass
class Conversation:
    """Conversation controls requests to EJ API and some validations during bot execution."""

    def __init__(self, tracker: Tracker, ej_conversation: dict = {}):
        self.tracker = tracker
        self.id = ej_conversation.get("id") or tracker.get_slot("conversation_id")
        self.title = ej_conversation.get("text") or tracker.get_slot(
            "conversation_title"
        )
        self.participant_can_add_comments = ej_conversation.get(
            "participants_can_add_comments"
        ) or tracker.get_slot("participant_can_add_comments")
        self.anonymous_votes_limit = ej_conversation.get(
            "anonymous_votes_limit"
        ) or tracker.get_slot("anonymous_votes_limit")
        self.ej_api = EjApi(self.tracker)

    @staticmethod
    def get(conversation_id: int, tracker: Tracker):
        ej_api = EjApi(tracker)
        try:
            response = ej_api.request(conversation_url(conversation_id))
            conversation = response.json()
            if len(conversation) == 0:
                raise EJCommunicationError
            if not conversation.get("id"):
                conversation["id"] = conversation_id
            return conversation
        except:
            raise EJCommunicationError

    def get_participant_statistics(self):
        try:
            url = user_statistics_url(self.id)
            response = self.ej_api.request(url)
            response = response.json()
        except:
            raise EJCommunicationError
        return response

    # TODO: refactor the try/except part to be a Python decorator.
    def get_next_comment(self):
        import time

        def _request():
            response = self.ej_api.request(url)
            if response.status_code == 500:
                raise EJCommunicationError
            comment = response.json()
            comment_url_as_list = comment["links"]["self"].split("/")
            comment["id"] = comment_url_as_list[len(comment_url_as_list) - 2]
            return comment

        url = conversation_random_comment_url(self.id)
        try:
            return _request()
        except EJCommunicationError:
            time.sleep(2)
        try:
            return _request()
        except Exception:
            raise EJCommunicationError

    @staticmethod
    def user_should_authenticate(
        has_completed_registration: bool, anonymous_votes_limit: int, statistics
    ):
        if not has_completed_registration:
            comments_counter = Conversation.get_user_voted_comments_counter(statistics)
            if comments_counter == anonymous_votes_limit:
                return True
        return False

    @staticmethod
    def available_comments_to_vote(statistics):
        return statistics["missing_votes"] >= 1

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

    @staticmethod
    def pause_to_ask_comment(vote_slot_value):
        return str(vote_slot_value).upper() == "PAUSA PARA PEDIR COMENTARIO"

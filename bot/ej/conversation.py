from dataclasses import dataclass
import logging

from actions.logger import custom_logger
from ej.ej_api import EjApi
from rasa_sdk import Tracker

from .routes import (
    random_comment_route,
    conversation_route,
    user_statistics_route,
)
from .settings import EJCommunicationError


logger = logging.getLogger(__name__)


@dataclass
class Conversation:
    """Conversation controls requests to EJ API and some validations during bot execution."""

    def __init__(self, tracker: Tracker, data: dict = {}):
        self.tracker = tracker
        self.data = data
        self.id = self._get_id()
        self.text = self._get_text()
        self.participant_can_add_comments = self._get_participants_can_add_comments()
        self.anonymous_votes_limit = self._get_anonymous_votes_limit()
        self.ej_api = EjApi(self.tracker)
        self.send_profile_question = self._get_send_profile_question()
        self.votes_to_send_profile_questions = int(
            self._get_votes_to_send_profile_questions()
        )

    def _get_votes_to_send_profile_questions(self):
        if self.data and "votes_to_send_profile_question" in self.data.keys():
            return self.data.get("votes_to_send_profile_question")
        return (
            self.tracker.get_slot("votes_to_send_profile_questions")
            if self.tracker.get_slot("votes_to_send_profile_questions")
            else 0
        )

    def _get_send_profile_question(self):
        if self.data and "send_profile_question" in self.data.keys():
            return self.data.get("send_profile_question")
        return self.tracker.get_slot("send_profile_questions")

    def _get_id(self):
        if self.data and "id" in self.data.keys():
            return self.data.get("id")
        return self.tracker.get_slot("conversation_id")

    def _get_text(self):
        if self.data and "text" in self.data.keys():
            return self.data.get("text")
        return self.tracker.get_slot("conversation_text")

    def _get_anonymous_votes_limit(self):
        if self.data and "anonymous_votes_limit" in self.data.keys():
            return self.data.get("anonymous_votes_limit")
        return self.tracker.get_slot("anonymous_votes_limit")

    def _get_participants_can_add_comments(self):
        if self.data and "participants_can_add_comments" in self.data.keys():
            return self.data.get("participants_can_add_comments")
        return self.tracker.get_slot("participant_can_add_comments")

    @staticmethod
    def get(conversation_id: int, tracker: Tracker):
        ej_api = EjApi(tracker)
        try:
            response = ej_api.request(conversation_route(conversation_id))
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
            url = user_statistics_route(self.id)
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
            if comment.get("content"):
                comment_url_as_list = comment["links"]["self"].split("/")
                comment["id"] = comment_url_as_list[len(comment_url_as_list) - 2]
                return comment
            return None

        url = random_comment_route(self.id)
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
            comments_counter = Conversation.get_voted_comments(statistics)
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
    def get_voted_comments(statistics):
        return statistics["comments"]

    @staticmethod
    def user_can_add_comment(statistics, tracker: Tracker) -> bool:
        participant_can_add_comments = tracker.get_slot("participant_can_add_comments")
        if not participant_can_add_comments:
            return False
        total_comments = Conversation.get_total_comments(statistics)
        voted_comments = Conversation.get_voted_comments(statistics)
        return (total_comments >= 4 and voted_comments == 4) or (
            total_comments < 4 and voted_comments == 2
        )

    @staticmethod
    def pause_to_ask_comment(vote_slot_value):
        return str(vote_slot_value).upper() == "PAUSA PARA PEDIR COMENTARIO"

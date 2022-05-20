import logging
import json
import requests

from .constants import *
from .routes import auth_headers

logger = logging.getLogger(__name__)


class Vote:
    """Vote controls voting requests to EJ API and some validations during bot execution."""

    def __init__(self, vote_slot_value, tracker):
        self.vote_slot_value = vote_slot_value
        self.channel = tracker.get_latest_input_channel()
        self.token = tracker.get_slot("ej_user_token")

    def is_valid(self):
        return str(self.vote_slot_value) in VALID_VOTE_VALUES

    def create(self, comment_id):
        if self.vote_slot_value in VOTE_CHOICES:
            choice = VOTE_CHOICES[self.vote_slot_value]
            body = json.dumps(
                {
                    "comment": comment_id,
                    "choice": choice,
                    "channel": self.channel,
                }
            )
            try:
                response = requests.post(
                    VOTES_URL,
                    data=body,
                    headers=auth_headers(self.token),
                )
                response = response.json()
                return response
            except Exception as e:
                raise EJCommunicationError

    @staticmethod
    def continue_voting():
        """
        Rasa end a form when all slots are filled. This method
        fill vote slot with None value, forcing the form to keep sending comments to user voting.
        """
        return {"vote": None}

    @staticmethod
    def stop_voting():
        """
        Rasa end a form when all slots are filled. This method
        fill vote slot with "parar" value, forcing the form to stop.

        On ActionFollowUpForm class, whe check if vote is == parar, if so,
        we send a utter finishing the conversation.
        """
        return {"vote": "parar"}

    @staticmethod
    def pause_voting_to_ask_phone_number():
        """
        Rasa end a form when all slots are filled. This method
        fill vote slot with "parar" value, forcing the form to stop.

        On ActionFollowUpForm class, whe check if vote is == PAUSAR PARA PEDIR TELEFONE, if so,
        we send a utter finishing the conversation.
        """
        return {"vote": "pausar para pedir telefone"}

    @staticmethod
    def pause_voting_to_ask_engaging():
        """
        Rasa end a form when all slots are filled. This method
        fill vote slot with "parar" value, forcing the form to stop.

        On ActionFollowUpForm class, whe check if vote is == PAUSAR PARA ENGAJAR, if so,
        we send a utter finishing the conversation.
        """
        return {"vote": "pausar para engajar"}

    def finished_voting(self):
        return {"vote": str(self.vote_slot_value).lower()}

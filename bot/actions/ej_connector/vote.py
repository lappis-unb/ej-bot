from dataclasses import dataclass
import json
from typing import Any, Text
from rasa_sdk import Tracker

import requests

from actions.logger import custom_logger
from rasa_sdk import Tracker

from .constants import *
from .routes import auth_headers


@dataclass
class Vote:
    """Vote controls voting requests to EJ API and some validations during bot execution."""

    vote_slot_value: Text
    tracker: Tracker
    channel: Text = ""
    token: Text = ""

    def __post_init__(self):
        self.channel = self.tracker.get_latest_input_channel()
        self.token = self.tracker.get_slot("access_token")

    def is_valid(self):
        return str(self.vote_slot_value) in VALID_VOTE_VALUES

    def create(self, comment_id):
        if self.is_valid():
            body = json.dumps(
                {
                    "comment": comment_id,
                    "choice": int(self.vote_slot_value),
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
                custom_logger(f"REGISTERED VOTE", data=response)
                return response
            except Exception as e:
                custom_logger(f"ERROR POSTING VOTE \n {e}")
                raise EJCommunicationError

    @staticmethod
    def continue_voting(tracker: Tracker):
        """
        Rasa ends a form when all slots are filled. This method
        fills vote slot with None value,
        forcing the form to keep sending comments to user voting.
        """
        return {
            "vote": None,
            "comment_confirmation": None,
            "comment": None,
            "access_token": tracker.get_slot("access_token"),
            "refresh_token": tracker.get_slot("refresh_token"),
        }

    @staticmethod
    def stop_voting():
        """
        Rasa end a form when all slots are filled. This method
        fill vote slot with "parar" value, forcing the form to stop.

        On ActionFollowUpForm class, whe check if vote is == parar, if so,
        we send a utter finishing the conversation.
        """
        return {"vote": "parar"}

    def finished_voting(self):
        return {"vote": str(self.vote_slot_value).lower()}

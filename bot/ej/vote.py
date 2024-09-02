from dataclasses import dataclass
from enum import Enum
import json
from typing import Text

import requests

from actions.logger import custom_logger
from rasa_sdk import Tracker
from rasa_sdk import Tracker

from .routes import auth_headers, votes_route
from .settings import *


class VoteDialogue:
    @staticmethod
    def continue_voting(tracker: Tracker):
        """
        Rasa ends a form when all slots are filled. This method
        fills the vote_form slots with None values,
        forcing Rasa to keep sending comments to voting.
        """
        return {
            "vote": None,
            "comment_confirmation": None,
            "comment": None,
            "access_token": tracker.get_slot("access_token"),
            "refresh_token": tracker.get_slot("refresh_token"),
        }

    @staticmethod
    def finish_voting():
        """
        Rasa ends a form when all slots are filled. This method
        fills the vote_form slots with '-' character,
        forcing Rasa to stop sending comments to voting.
        """
        return {"vote": "-", "comment_confirmation": "-", "comment": "-"}


class VoteChoices(Enum):
    AGREE = "1"
    DISAGREE = "-1"
    SKIP = "0"


@dataclass
class Vote:
    """Vote controls voting requests to EJ API and some validations during bot execution."""

    vote_slot_value: Text
    tracker: Tracker
    channel: Text = ""
    token: Text = ""

    def __post_init__(self):
        input_channel = self.tracker.get_latest_input_channel()
        if input_channel == "cmdline":
            self.channel = "unknown"
        else:
            self.channel = input_channel
        self.token = self.tracker.get_slot("access_token")

    def is_valid(self):
        """
        return true if vote_slot_value is equal to on of VALID_VOTE_VALUES values.
        """
        try:
            return VoteChoices(self.vote_slot_value)
        except Exception as e:
            return False

    def is_internal(self):
        """
        return true if vote_slot_value is equall to '-'.
        The '-' character is used to stop the vote form and request a new EJ conversation.
        """
        return str(self.vote_slot_value) == "-"

    def create(self, comment_id):
        import time

        def _request():
            body = json.dumps(
                {
                    "comment": comment_id,
                    "choice": int(self.vote_slot_value),
                    "channel": self.channel,
                }
            )
            response = requests.post(
                votes_route(),
                data=body,
                headers=auth_headers(self.token),
            )
            response = response.json()
            custom_logger(f"REGISTERED VOTE", data=response)
            return response

        if self.is_valid():
            try:
                return _request()
            except Exception as e:
                time.sleep(2)
            try:
                return _request()
            except Exception as e:
                custom_logger(f"ERROR POSTING VOTE \n {e}")
                raise EJCommunicationError

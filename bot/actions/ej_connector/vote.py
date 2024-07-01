import json
import requests

from dataclasses import dataclass
from typing import Any, Text

from rasa_sdk import Tracker
from rasa_sdk.events import SlotSet, ActiveLoop

from actions.logger import custom_logger

from .constants import *
from .ej_api import EjApi


@dataclass
class Vote:
    """Vote controls voting requests to EJ API and some validations during bot execution."""

    def __init__(self, vote_slot_value, tracker: Tracker):
        self.tracker = tracker
        self.vote_slot_value = vote_slot_value
        self.ej_api = EjApi(tracker)
        self.__post_init__()

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
                response = self.ej_api.request(url=VOTES_URL, payload=body)

                response = response.json()
                custom_logger(f"REGISTERED VOTE", data=response)
                return response
            except Exception as e:
                custom_logger(f"ERROR POSTING VOTE \n {e}")
                raise EJCommunicationError

    @staticmethod
    def clear_slots():
        return [
            SlotSet("vote", None),
            SlotSet("comment_confirmation", None),
            SlotSet("comment", None),
        ]

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
    def need_help():
        response = Vote.clear_slots()
        response += [
            ActiveLoop(None),
            SlotSet("user_need_help", True),
        ]
        return response

    @staticmethod
    def stop_voting():
        response = Vote.clear_slots()
        response += [
            ActiveLoop(None),
            SlotSet("user_want_stop_vote", True),
        ]
        return response

    @staticmethod
    def user_limit_anonymous_vote():
        response = Vote.clear_slots()
        response += [
            ActiveLoop(None),
            SlotSet("user_reached_max_anonymous_votes", True),
        ]
        return response

    @staticmethod
    def user_reached_max_votes():
        response = Vote.clear_slots()
        response += [
            ActiveLoop(None),
            SlotSet("user_reached_max_votes", True),
        ]
        return response

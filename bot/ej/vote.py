from dataclasses import dataclass
from enum import Enum
import json
from typing import Any, Dict, List, Text

import requests

from actions.logger import custom_logger
from rasa_sdk import Tracker
from rasa_sdk.events import FollowupAction, SlotSet

from .routes import auth_headers, votes_route
from .settings import *


class SlotsType(Enum):
    DICT = "dict"
    LIST = "list"


class VoteChoices(Enum):
    AGREE = "1"
    DISAGREE = "-1"
    SKIP = "0"
    DEACTIVATE_VOTE_FORM = "-"


class VoteDialogue:
    @staticmethod
    def restart_vote_form_slots():
        """
        Rasa ends a form when all slots are filled. This method
        fills the vote_form slots with None values,
        forcing Rasa to keep sending comments to voting.
        """
        return {"vote": None}

    @staticmethod
    def deactivate_vote_form_slots(
        slot_type: SlotsType = SlotsType.DICT,
    ) -> Dict[Any, Any] | List[Any]:
        """
        Rasa ends a form when all slots are filled. This method
        fills the vote_form slots with '-' character,
        forcing Rasa to stop sending comments to voting.
        """
        match slot_type:
            case SlotsType.DICT:
                return {"vote": "-"}
            case SlotsType.LIST:
                return [SlotSet("vote", "-")]
            case _:
                raise Exception

    @staticmethod
    def completed_vote_form_slots(slot_type: SlotsType) -> dict | List[Any]:
        """
        Returns slots to deactive the vote_form when the participant voted in all
        available comments.
        """
        stop_voting_slots = VoteDialogue.deactivate_vote_form_slots(slot_type)
        match slot_type:
            case SlotsType.DICT:
                return {**stop_voting_slots, "participant_voted_in_all_comments": True}
            case SlotsType.LIST:
                return stop_voting_slots + [
                    SlotSet("participant_voted_in_all_comments", True),
                    FollowupAction("action_deactivate_loop"),
                ]
            case _:
                raise Exception


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

    @staticmethod
    def is_valid(vote_option):
        """
        return true if vote_option is equal to on of VALID_VOTE_VALUES values.
        """
        try:
            return VoteChoices(vote_option)
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

        if VoteChoices.DEACTIVATE_VOTE_FORM.value == self.vote_slot_value:
            return

        if Vote.is_valid(self.vote_slot_value):
            try:
                return _request()
            except Exception as e:
                time.sleep(2)
            try:
                return _request()
            except Exception as e:
                custom_logger(f"ERROR POSTING VOTE \n {e}")
                raise EJCommunicationError

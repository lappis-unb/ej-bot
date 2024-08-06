from dataclasses import dataclass
from typing import Any
from ej.vote import VoteDialogue
from rasa_sdk.events import SlotSet, FollowupAction


@dataclass
class EJApiErrorManager:
    def get_slots(self, as_dict=False) -> Any:
        if as_dict:
            finish_voting_slots = VoteDialogue.finish_voting()
            return {**finish_voting_slots, "ej_api_connection_error": True}
        return [
            SlotSet("vote", "-"),
            SlotSet("comment", "-"),
            SlotSet("comment_confirmation", "-"),
            SlotSet("ej_api_connection_error", True),
            FollowupAction("utter_ej_communication_error"),
        ]

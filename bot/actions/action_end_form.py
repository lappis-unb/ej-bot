from typing import Any, Dict, List, Text

from actions.logger import custom_logger
from rasa_sdk import Action, Tracker
from rasa_sdk.events import EventType, ActiveLoop
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict


class ActionStopForm(Action):
    """
    Documentation
    """

    def name(self) -> Text:
        return "action_stop_vote"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:

        custom_logger("Running action_stop_vote")

        return [ActiveLoop(None)]

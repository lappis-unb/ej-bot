from enum import Enum
from typing import Any, Dict, Text, Callable
from rasa_sdk import Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import FollowupAction, ActiveLoop
from functools import wraps
from actions.logger import custom_logger


class Intent(Enum):
    CHECK_AUTHENTICATION = "check_authentication"
    STOP = "stop"
    HELP = "help"


def check_intent(intent_names: list[Intent]):
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(
            self,
            slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
        ):
            custom_logger(f"Checking intent {intent_names}")
            latest_intent = tracker.latest_message["intent"].get("name")
            custom_logger(f"Latest intent: {latest_intent}")
            if latest_intent in [intent.value for intent in intent_names]:
                if latest_intent == Intent.CHECK_AUTHENTICATION.value:
                    return [ActiveLoop(None), FollowupAction("action_stop_vote")]
                if latest_intent == Intent.STOP.value:
                    return [ActiveLoop(None), FollowupAction("action_stop_vote")]
                if latest_intent == Intent.HELP.value:
                    return [ActiveLoop(None), FollowupAction("action_stop_vote")]
            return func(self, slot_value, dispatcher, tracker, domain)

        return wrapper

    return decorator

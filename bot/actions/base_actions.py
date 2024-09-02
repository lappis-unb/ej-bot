from dataclasses import dataclass, field
from typing import Any, List


class CheckersMixin:
    def __init__(self):
        self.slots = []

    def get_checkers(self, tracker, **kwargs):
        raise NotImplementedError


@dataclass
class CheckSlotsInterface:
    """
    Defines a common interface to verify an action slots.
    """

    tracker: Any = None
    dispatcher: Any = None
    conversation: Any = None
    conversation_statistics: Any = None
    slots: List[Any] = field(default_factory=list)
    slot_value: Any = ""

    def should_return_slots_to_rasa(self) -> bool:
        """
        Returns True if the dialogue slots has to be updated.
        If True, the slots field must be updated with the corresponding SlotSet or FollowupAction.
        """
        raise Exception("not implemented")

    def _dispatch_messages(self):
        pass

    def set_slots(self):
        raise Exception("not implemented")

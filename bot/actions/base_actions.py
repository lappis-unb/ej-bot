from dataclasses import dataclass, field
from typing import Any, Dict, List, Text

from ej.user import User


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
    slots: List[Any] | Dict[Any, Any] = field(default_factory=list)
    slot_value: Any = ""
    slot_type: Text = "dict"
    user: User = field(default_factory=lambda: User(None))

    def __str__(self):
        return f"Checker: {self.__class__.__name__}"

    def __repr__(self):
        return f"Checker: {self.__class__.__name__}"

    def has_slots_to_return(self) -> bool:
        """
        Returns True if the dialogue slots has to be updated.
        If True, the slots field must be updated with the corresponding SlotSet or FollowupAction.
        """
        raise Exception("not implemented")

    def _dispatch_messages(self):
        pass

    def set_slots(self):
        raise Exception("not implemented")

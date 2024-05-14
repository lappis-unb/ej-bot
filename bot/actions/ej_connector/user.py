import json
from typing import Any, Text

import requests

from actions.logger import custom_logger

from .constants import *


class User(object):
    """
    For telegram channel, tracker_sender_id is the unique ID from the user talking with the bot.
    """

    ANONYMOUS_USER_NAME = "Participante anônimo"

    def __init__(self, tracker_sender_id, name=ANONYMOUS_USER_NAME):
        self.name = name
        self.display_name = name
        self.tracker_sender_id = tracker_sender_id
        self.password = f"{self.remove_special(tracker_sender_id)}-opinion-bot"
        self.password_confirm = f"{self.remove_special(tracker_sender_id)}-opinion-bot"
        self._set_email()

    def serialize(self):
        return json.dumps(self.__dict__)

    def _set_email(self):
        if self.name != User.ANONYMOUS_USER_NAME:
            self.email = f"{self.name}-opinion-bot@mail.com"
        self.email = (
            f"{self.remove_special(self.tracker_sender_id)}-opinion-bot@mail.com"
        )

    def authenticate(self):
        """
        Differentiate user type of login (using phone number or anonymous)
        providing the current flow for conversation
        """
        custom_logger(f"creating new user", data=self.__dict__)
        response = None
        try:
            response = self._get_or_create_user(AUTH_URL, self.serialize())
            self.token = response.json()["token"]
        except Exception:
            response = self._get_or_create_user(REGISTRATION_URL, self.serialize())
            self.token = response.json()["token"]
        except:
            raise Exception("COULD NOT CREATE USER")

    def _get_or_create_user(self, url: Text, payload: Any) -> Any:
        return requests.post(
            url,
            data=payload,
            headers=HEADERS,
        )

    @staticmethod
    def get_name_from_tracker_state(state: dict):
        latest_message = state["latest_message"]
        metadata = latest_message["metadata"]
        if metadata:
            return metadata.get("user_name")
        return User.ANONYMOUS_USER_NAME

    def remove_special(self, line):
        for char in ":+":
            line = line.replace(char, "")
        return line

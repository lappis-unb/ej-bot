import json
from typing import Any, Text

import requests

from actions.logger import custom_logger
from actions.ej_connector.ej_api import EjApi

from .constants import *


class User(object):
    """
    For telegram channel, tracker_sender_id is the unique ID from the user talking with the bot.
    """

    ANONYMOUS_USER_NAME = "Participante anônimo"

    def __init__(self, tracker: Any, name=ANONYMOUS_USER_NAME):
        self.name = name
        self.display_name = name
        self.tracker_sender_id = tracker.sender_id
        self.password = f"{self.remove_special(tracker.sender_id)}-opinion-bot"
        self.password_confirm = f"{self.remove_special(tracker.sender_id)}-opinion-bot"
        self.ej_api = EjApi(tracker)
        self.tracker = tracker
        self._set_email()

    def serialize(self):
        return json.dumps(
            {
                "name": self.name,
                "display_name": self.display_name,
                "password": self.password,
                "password_confirm": self.password_confirm,
                "email": self.email,
            }
        )

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
        access_token = self.tracker.get_slot("access_token")
        refresh_token = self.tracker.get_slot("refresh_token")
        custom_logger(f"TOKENS: {access_token} {refresh_token}")
        if access_token and refresh_token:
            return self.tracker

        custom_logger(f"creating new user", data=self.serialize())
        response = None
        try:
            response = self.ej_api.request(AUTH_URL, self.serialize())
            access_token = response.json()["access_token"]
            refresh_token = response.json()["refresh_token"]
        except Exception:
            response = self.ej_api.request(REGISTRATION_URL, self.serialize())
            access_token = response.json()["access_token"]
            refresh_token = response.json()["refresh_token"]
        except:
            raise Exception("COULD NOT CREATE USER")

        self.tracker.slots["access_token"] = access_token
        self.tracker.slots["refresh_token"] = refresh_token

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

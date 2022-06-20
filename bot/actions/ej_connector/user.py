import os
import json
import logging
import requests
from .constants import *
from ..utils import remove_special

logger = logging.getLogger(__name__)


class User(object):
    """
    For telegram channel, tracker_sender_id is the unique ID from the user talking with the bot.
    """

    ANONYMOUS_USER_NAME = "Participante anônimo"

    def __init__(self, tracker_sender_id, name=ANONYMOUS_USER_NAME):
        self.name = name
        self.display_name = name
        self.tracker_sender_id = tracker_sender_id
        self.password = f"{remove_special(tracker_sender_id)}-opinion-bot"
        self.password_confirm = f"{remove_special(tracker_sender_id)}-opinion-bot"
        self._set_email()

    def serialize(self):
        return json.dumps(self.__dict__)

    def _set_email(self):
        if self.name != User.ANONYMOUS_USER_NAME:
            self.email = f"{self.name}-opinion-bot@mail.com"
        self.email = f"{remove_special(self.tracker_sender_id)}-opinion-bot@mail.com"

    def authenticate(self):
        """
        Differentiate user type of login (using phone number or anonymous)
        providing the current flow for conversation
        """
        self.get_or_create_user()

    def get_or_create_user(self):
        logger.debug("CREATING NEW USER")
        logger.debug(self.serialize())
        try:
            response = requests.post(
                REGISTRATION_URL,
                data=self.serialize(),
                headers=HEADERS,
            )
            self.token = response.json()["token"]
        except:
            raise EJCommunicationError

    @staticmethod
    def get_name_from_tracker_state(state: dict):
        latest_message = state["latest_message"]
        metadata = latest_message["metadata"]
        if metadata:
            return metadata.get("user_name")
        return User.ANONYMOUS_USER_NAME

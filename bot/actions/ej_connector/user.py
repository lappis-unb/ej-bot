from bot.actions.utils import remove_special
import os
import json
import logging
import requests
from .constants import *

logger = logging.getLogger(__name__)


class User(object):
    """
    For telegram channel, tracker_sender_id is the unique ID from the user talking with the bot.
    """

    def __init__(self, tracker_sender_id, name="Participante anônimo", phone_number=""):
        self.name = name
        self.display_name = ""
        self.phone_number = phone_number
        self.tracker_sender_id = tracker_sender_id
        self.email = f"{remove_special(tracker_sender_id)}-rasa@mail.com"
        self.password = f"{remove_special(tracker_sender_id)}-rasa"
        self.password_confirm = f"{remove_special(tracker_sender_id)}-rasa"

    def serialize(self):
        return json.dumps(self.__dict__)

    def authenticate(self, last_intent):
        """
        Differentiate user type of login (using phone number or anonymous)
        providing the current flow for conversation
        """
        if self.phone_number and last_intent == "phone_number":
            utter_name = "utter_got_phone_number"
        else:
            utter_name = "utter_user_want_anonymous"

        self.get_or_create_user()
        self.authenticate_utter = utter_name

    def get_or_create_user(self):
        logger.debug("CREATING NEW USER")
        logger.debug(self.serialize())
        try:
            response = requests.post(
                REGISTRATION_URL,
                data=self.serialize(),
                headers=HEADERS,
            )
            self.token = response.json()["key"]
        except:
            raise EJCommunicationError

from dataclasses import dataclass
import json
from typing import Any, Text, Dict
import hashlib
from datetime import datetime, timezone
from datetime import timedelta
import jwt

from actions.logger import custom_logger
from ej.ej_api import EjApi

from .constants import *


TOKEN_EXPIRATION_TIME = timedelta(minutes=10)
JWT_SECRET = os.getenv("JWT_SECRET")
SECRET_KEY = os.getenv("SECRET_KEY")
EXTERNAL_AUTHENTICATION_HOST = os.getenv("EXTERNAL_AUTHENTICATION_HOST", "")


class CheckAuthenticationDialogue:

    END_PARTICIPATION_SLOT = "end_participant_conversation"
    CHECK_AUTHENTICATION_SLOT = "check_participant_authentication"

    @staticmethod
    def get_message():
        buttons = [
            {
                "title": "Confirmar",
                "payload": CheckAuthenticationDialogue.CHECK_AUTHENTICATION_SLOT,
            },
            {
                "title": "Encerrar",
                "payload": CheckAuthenticationDialogue.END_PARTICIPATION_SLOT,
            },
        ]
        return {
            "text": "Estou aguardando você se autenticar para continuar a votação. 😊",
            "buttons": buttons,
        }

    @staticmethod
    def restart_auth_form() -> Dict:
        return {"check_authentication": None, "has_completed_registration": None}

    @staticmethod
    def end_auth_form() -> Dict:
        return {
            "check_authentication": CheckAuthenticationDialogue.END_PARTICIPATION_SLOT,
            "has_completed_registration": False,
        }

    @staticmethod
    def participant_refuses_to_auth(slot_value: Text):
        return slot_value == CheckAuthenticationDialogue.END_PARTICIPATION_SLOT


@dataclass
class ExternalAuthorizationService:

    sender_id: Text
    secret_id: Text

    def get_authentication_link(self):
        jwt_data = self._get_jwt_authorization_data()
        authorization_url = self._get_authorization_url()
        return f"{authorization_url}?user_data={jwt_data}"

    def _get_jwt_authorization_data(
        self,
        expiration_minutes=TOKEN_EXPIRATION_TIME.total_seconds(),
    ) -> Text:
        utc_now = datetime.now(timezone.utc)
        expiration = utc_now + timedelta(minutes=expiration_minutes)
        data = {
            "user_id": self.sender_id,
            "secret_id": self.secret_id,
            "exp": expiration,
        }
        encoded_data = jwt.encode(data, JWT_SECRET, algorithm="HS256")
        return encoded_data

    def _get_authorization_url(self):
        return f"{EXTERNAL_AUTHENTICATION_HOST}/processes/testeplanocultura/f/1192/link_external_user"

    @staticmethod
    def generate_hash(identifier):
        hash_object = hashlib.sha256(identifier.encode())
        hex_dig = hash_object.hexdigest()
        return hex_dig


class User(object):
    """
    For telegram channel, tracker_sender_id is the unique ID from the user talking with the bot.
    """

    ANONYMOUS_USER_NAME = "Participante anônimo"

    def __init__(self, tracker: Any, name=ANONYMOUS_USER_NAME):
        self.name = name
        self.display_name = name
        self.tracker_sender_id = tracker.sender_id
        self.ej_api = EjApi(tracker)
        self.tracker = tracker
        self.secret_id = ExternalAuthorizationService.generate_hash(tracker.sender_id)
        self.has_completed_registration = tracker.get_slot("has_completed_registration")
        self._set_password()
        self._set_email()

    def _set_password(self):
        password = self._get_password_hash()
        self.password, self.password_confirm = [password, password]

    def _get_password_hash(self):
        if SECRET_KEY and self.tracker_sender_id:
            combined = f"{self.tracker_sender_id}{SECRET_KEY}"
            hash_object = hashlib.sha256(combined.encode())
            return hash_object.hexdigest()
        raise Exception("could not generate user password")

    def registration_data(self):
        return json.dumps(
            {
                "name": self.name,
                "display_name": self.display_name,
                "password": self.password,
                "password_confirm": self.password_confirm,
                "email": self.email,
                "secret_id": self.secret_id,
                "has_completed_registration": False,
            }
        )

    def auth_data(self):
        return json.dumps(
            {
                "name": self.name,
                "display_name": self.display_name,
                "password": self.password,
                "password_confirm": self.password_confirm,
                "email": self.email,
                "secret_id": self.secret_id,
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

        response = None
        try:
            custom_logger(
                f"Requesting new token for the participant", data=self.auth_data()
            )
            response = self.ej_api.request(AUTH_URL, self.auth_data())
            if response.status_code != 200:
                custom_logger(f"EJ API ERROR", data=response.json())
                raise Exception
        except Exception:
            custom_logger(
                f"Failed to request token, trying to create the participant",
                data=self.registration_data(),
            )
            response = self.ej_api.request(REGISTRATION_URL, self.registration_data())
            if response.status_code != 201:
                custom_logger(f"EJ API ERROR", data=response.json())
                raise Exception("COULD NOT CREATE USER")

        custom_logger(f"EJ API RESPONSE", data=response.json())
        response_data = response.json()
        self.tracker.slots["access_token"] = response_data["access_token"]
        self.tracker.slots["refresh_token"] = response_data["refresh_token"]
        self.has_completed_registration = response_data["has_completed_registration"]
        self.tracker.slots[
            "has_completed_registration"
        ] = self.has_completed_registration

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

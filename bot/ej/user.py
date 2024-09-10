import base64
from dataclasses import dataclass
from datetime import datetime, timezone
from datetime import timedelta
import hashlib
import json
from typing import Any, Dict, Text

import jwt

from actions.logger import custom_logger
from ej.ej_client import EjClient

from .routes import auth_route, registration_route
from .settings import (
    BP_EJ_COMPONENT_ID,
    EXTERNAL_AUTHENTICATION_HOST,
    JWT_SECRET,
    SECRET_KEY,
    TOKEN_EXPIRATION_TIME,
)


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
class ExternalAuthenticationManager:
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
        """
        Returns a JWT string containing the user_id and secret_id fields.
        This token will be used by Brasil Particiativo platform to unify the
        the data (votes, comments and profile fields) provided by the same user across different channels.
        """
        if not JWT_SECRET:
            raise Exception("JWT_SECRET variable not found.")

        utc_now = datetime.now(timezone.utc)
        expiration = utc_now + timedelta(minutes=expiration_minutes)
        data = {
            "user_id": self.sender_id,
            "secret_id": self.secret_id,
            "exp": expiration,
        }
        return jwt.encode(data, JWT_SECRET, algorithm="HS256")

    def _get_authorization_url(self) -> Text:
        """
        Returns an URL to authenticate the user using the JWT authorization data.
        """
        if not EXTERNAL_AUTHENTICATION_HOST or not BP_EJ_COMPONENT_ID:
            raise Exception(
                "EXTERNAL_AUTHENTICATION_HOST or BP_EJ_COMPONENT_ID variables were not defined"
            )

        return f"{EXTERNAL_AUTHENTICATION_HOST}/{BP_EJ_COMPONENT_ID}/link_external_user"

    @staticmethod
    def to_sha256(sender_id: Text):
        """
        Crypto sender_id with sha256 algorithm.
        """
        hash_object = hashlib.sha256(sender_id.encode())
        hex_dig = hash_object.hexdigest()
        return hex_dig


class User:
    """
    For telegram channel, tracker_sender_id is the unique ID from the user talking with the bot.
    """

    ANONYMOUS_USER_NAME = "Participante anônimo"

    def __init__(self, tracker: Any):
        if tracker:
            self.tracker = tracker
            self.sender_id = tracker.sender_id
            self.has_completed_registration = tracker.get_slot(
                "has_completed_registration"
            )
            self.name = self._get_name_from_tracker()
            self.display_name = self.name
            self.email = f"{self.remove_special(self.sender_id)}-opinion-bot@mail.com"
            self.password = self._get_password()
            self.password_confirm = self.password
            self.secret_id = ExternalAuthenticationManager.to_sha256(self.sender_id)
            self.ej_client = EjClient(tracker)

    def _get_password(self):
        if SECRET_KEY and self.sender_id:
            seed = f"{self.sender_id}{SECRET_KEY}".encode()
            seed_base64 = base64.b64encode(seed)
            return hashlib.sha256(seed_base64).hexdigest()
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
            response = self.ej_client.request(auth_route(), self.auth_data())
            if response.status_code != 200:
                custom_logger(f"EJ API ERROR", data=response.json())
                raise Exception
        except Exception:
            custom_logger(
                f"Failed to request token, trying to create the participant",
                data=self.registration_data(),
            )
            response = self.ej_client.request(
                registration_route(), self.registration_data()
            )
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

    def _get_name_from_tracker(self):
        metadata = self.tracker.latest_message.get("metadata")
        if metadata:
            if metadata.get("user_name"):
                return metadata.get("user_name")
            elif metadata.get("contact_name"):
                return metadata.get("contact_name")
        return User.ANONYMOUS_USER_NAME

    def remove_special(self, line):
        for char in ":+":
            line = line.replace(char, "")
        return line

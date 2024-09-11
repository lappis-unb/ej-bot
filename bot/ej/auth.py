from dataclasses import dataclass
from datetime import datetime, timezone
from datetime import timedelta
import hashlib
from typing import Dict, Text

import jwt

from .settings import (
    BP_EJ_COMPONENT_ID,
    EXTERNAL_AUTHENTICATION_HOST,
    JWT_SECRET,
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

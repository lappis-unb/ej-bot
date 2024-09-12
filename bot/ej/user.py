import base64
import hashlib
import json
from typing import Any, Text

from actions.logger import custom_logger
from ej.auth import ExternalAuthenticationManager
from ej.ej_client import EjClient

from .routes import auth_route, registration_route
from .settings import (
    SECRET_KEY,
)


class User:
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
            ruby_compatible_base64 = self.get_base64_ruby_compatible_format(
                seed_base64.decode()
            )
            return hashlib.sha256(ruby_compatible_base64.encode()).hexdigest()
        raise Exception("could not generate user password")

    def get_base64_ruby_compatible_format(self, seed_base64: Text):
        """
         this is a hack to generate the same Decidim-encoded string for the user password.
         Every 60 characters, we need to insert a \n character in the Python base64-encoded string.
         Also, a \n character must be inserted at the end.

        https://ruby-doc.org/stdlib-2.5.3/libdoc/base64/rdoc/Base64.html
        """
        ruby_compatible_base64 = ""
        for count, char in enumerate(list(seed_base64)):
            ruby_compatible_base64 += char
            if not (count + 1) % 60:
                ruby_compatible_base64 += "\n"
        ruby_compatible_base64 += "\n"
        return ruby_compatible_base64

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

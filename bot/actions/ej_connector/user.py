import json
import os
from typing import Any, Text
import requests
import hashlib
from dotenv import load_dotenv
from cryptography.fernet import Fernet
import jwt
from datetime import datetime, timedelta, timezone

from actions.logger import custom_logger
from .constants import *

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")
SECRET_KEY = os.getenv("SECRET_KEY")


class User(object):
    """
    For telegram channel, tracker_sender_id is the unique ID from the user talking with the bot.
    """

    ANONYMOUS_USER_NAME = "Participante anônimo"

    def __init__(self, tracker: Any, name=ANONYMOUS_USER_NAME):
        self.name = name
        self.display_name = name
        self.tracker_sender_id = tracker.sender_id
        self.password = self._generate_hash_password(f"{tracker.sender_id}")
        self.password_confirm = self._generate_hash_password(f"{tracker.sender_id}")
        self.tracker = tracker
        self._set_email()
        self.secret_id = self._generate_hash(self.tracker_sender_id)
        self.anonymous = self._set_anonymous()

    def _set_anonymous(self):
        response = self.get_user()
        if response.status_code == 200:
            data = response.json()
            return data.get("anonymous")
        else:
            return True

    def serialize(self):
        if self.secret_id is None:
            self.secret_id = self._generate_hash(self.tracker_sender_id)

        data = {
            "name": self.name,
            "display_name": self.display_name,
            "password": self.password,
            "password_confirm": self.password_confirm,
            "email": self.email,
            "secret_id": self.secret_id,
            "anonymous": self.anonymous,
        }

        return json.dumps(data)

    def serialize_auth(self):
        if self.secret_id is None:
            self.secret_id = self._generate_hash(self.tracker_sender_id)

        data = {
            "secret_id": self.secret_id,
            "password": self.password,
        }

        return json.dumps(data)

    def _set_email(self):
        if self.name != User.ANONYMOUS_USER_NAME:
            self.email = f"{self.name}-opinion-bot@mail.com"
        else:
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
            custom_logger(f"try authentication")
            auth_serializer = self.serialize_auth()
            custom_logger(f"auth_serializer: {auth_serializer}")
            response = self.auth_user()
            data = response.json()
            custom_logger(f"response: {data}")
            access_token = data["access_token"]
            refresh_token = data["refresh_token"]

            if data["name"]:
                self.name = data["name"]
                self.email = data["email"]
        except Exception as e:
            custom_logger(f"Authentication failed: {e}")
            try:
                custom_logger(f"try registration")
                user_serializer = self.serialize()
                custom_logger(f"user_serializer: {user_serializer}")
                response = self.register_user()
                data = response.json()
                custom_logger(f"response: {data}")
                access_token = data["access_token"]
                refresh_token = data["refresh_token"]
            except Exception as e:
                custom_logger(f"Registration failed: {e}")
                raise Exception("COULD NOT CREATE USER")

        self.tracker.slots.update(
            {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user_name": self.name,
                "secret_id": self.secret_id,
            }
        )
        return self.tracker

    def get_user(self):
        url = f"{GET_USER_URL}?secret_id={self.secret_id}"
        return requests.get(
            url,
            headers=HEADERS,
        )

    def register_user(self):
        user_serializer = self.serialize()
        return requests.post(
            REGISTRATION_URL,
            user_serializer,
            headers=HEADERS,
        )

    def auth_user(self):
        auth_serializer = self.serialize_auth()
        return requests.post(
            AUTH_URL,
            auth_serializer,
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

    @staticmethod
    def _generate_hash(identifier):
        hash_object = hashlib.sha256(identifier.encode())
        hex_dig = hash_object.hexdigest()
        return hex_dig

    @staticmethod
    def generate_access_token(user_id, secret_id, expiration_minutes=5):
        utc_now = datetime.now(timezone.utc)
        expiration = utc_now + timedelta(minutes=expiration_minutes)
        payload = {"user_id": user_id, "secret_id": secret_id, "exp": expiration}
        token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
        return token

    def _generate_hash_password(self, seed):
        combined = f"{seed}{SECRET_KEY}"
        hash_object = hashlib.sha256(combined.encode())
        hex_dig = hash_object.hexdigest()
        return hex_dig


def generate_secret_key():
    secret_key = Fernet.generate_key()
    return secret_key.decode()

import json
import logging
from typing import Text

import requests

from rasa_sdk import Tracker

from .constants import *
from .ej_api import EjApi

logger = logging.getLogger(__name__)


class Comment:
    """Comment controls commenting requests to EJ API and some validations during bot execution."""

    def __init__(self, conversation_id: str, comment_text: str, tracker: Tracker):
        self.conversation_id = conversation_id
        self.text = comment_text
        self.token = tracker.get_slot("access_token")
        self.ej_api = EjApi(tracker)

    def create(self):
        if len(self.text) > 3:
            body = json.dumps(
                {
                    "content": self.text,
                    "conversation": self.conversation_id,
                    "status": "pending",
                }
            )
            try:
                response = self.ej_api.request(url=COMMENTS_URL, payload=body)

                response = response.json()
            except Exception as e:
                raise EJCommunicationError
            return response

    @staticmethod
    def pause_to_ask_comment(vote_option: Text):
        return {
            "vote": vote_option,
            "comment_confirmation": None,
            "comment": None,
        }

    @staticmethod
    def resume_voting(slot_value: Text):
        return {
            "vote": None,
            "comment_confirmation": slot_value,
            "comment": "",
        }

    @staticmethod
    def get_utter(metadata, comment_title):
        if metadata and "agent" in metadata:
            return Comment.get_livechat_utter(comment_title)
        return Comment.get_buttons_utter(comment_title)

    @staticmethod
    def get_livechat_utter(comment_title):
        # channel is livechat, can't render buttons
        return {"text": comment_title}

    @staticmethod
    def get_buttons_utter(comment_title):
        buttons = [
            {"title": "Concordar", "payload": "1"},
            {"title": "Discordar", "payload": "-1"},
            {"title": "Pular", "payload": "0"},
        ]
        return {"text": comment_title, "buttons": buttons}

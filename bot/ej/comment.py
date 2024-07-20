import json
import logging
from typing import Text

import requests

from rasa_sdk import Tracker

from .constants import *
from .routes import auth_headers

logger = logging.getLogger(__name__)


class CommentDialogue:

    REFUSES_TO_ADD_COMMENT = "não"
    WANTS_TO_ADD_COMMENT = "sim"

    @staticmethod
    def user_refuses_to_add_comment(slot_value):
        return slot_value == CommentDialogue.REFUSES_TO_ADD_COMMENT

    @staticmethod
    def user_wants_to_add_comment(slot_value):
        return slot_value == CommentDialogue.WANTS_TO_ADD_COMMENT

    @staticmethod
    def ask_user_to_comment(vote_option: Text):
        return {"vote": vote_option, "comment_confirmation": None, "comment": None}

    @staticmethod
    def resume_voting(slot_value: Text):
        return {"vote": None, "comment_confirmation": slot_value, "comment": ""}

    @staticmethod
    def get_utter(metadata, comment_title):
        if metadata and "agent" in metadata:
            return CommentDialogue.get_livechat_utter(comment_title)
        return CommentDialogue.get_buttons_utter(comment_title)

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


class Comment:
    """Comment controls commenting requests to EJ API and some validations during bot execution."""

    def __init__(self, conversation_id: str, comment_text: str, tracker: Tracker):
        self.conversation_id = conversation_id
        self.text = comment_text
        self.token = tracker.get_slot("access_token")

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
                response = requests.post(
                    COMMENTS_URL,
                    data=body,
                    headers=auth_headers(self.token),
                )
                response = response.json()
            except Exception as e:
                raise EJCommunicationError
            return response

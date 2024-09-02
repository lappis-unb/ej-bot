import json
import logging
from typing import Text

import requests

from rasa_sdk import Tracker

from .routes import auth_headers, comments_route
from .settings import *

logger = logging.getLogger(__name__)


class CommentDialogue:

    REFUSES_TO_ADD_COMMENT = "não"
    WANTS_TO_ADD_COMMENT = "sim"
    BUTTONS = [
        {"title": "Concordar", "payload": "1"},
        {"title": "Discordar", "payload": "-1"},
        {"title": "Pular", "payload": "0"},
    ]

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
    def get_comment_message(comment_content, user_voted_comments, total_comments):
        return (
            f"*{comment_content}* \n O que você acha disso? \n\n"
            f"{user_voted_comments + 1} de {total_comments} comentários."
        )

    @staticmethod
    def get_utter_message(
        metadata, comment_content, user_voted_comments, total_comments
    ):
        comment_message = CommentDialogue.get_comment_message(
            comment_content, user_voted_comments, total_comments
        )
        if metadata and "agent" in metadata:
            return CommentDialogue.get_livechat_utter(comment_message)
        return CommentDialogue.get_utter_with_buttons(comment_message)

    @staticmethod
    def get_livechat_utter(comment_title):
        # channel is livechat, can't render buttons
        return {"text": comment_title}

    @staticmethod
    def get_utter_with_buttons(comment_title):
        return {"text": comment_title, "buttons": CommentDialogue.BUTTONS}


class Comment:
    """Comment controls commenting requests to EJ API and some validations during bot execution."""

    def __init__(self, conversation_id: str, comment_content: str, tracker: Tracker):
        self.conversation_id = conversation_id
        self.content = comment_content
        self.token = tracker.get_slot("access_token")

    def create(self):
        if len(self.content) > 3:
            body = json.dumps(
                {
                    "content": self.content,
                    "conversation": self.conversation_id,
                    "status": "pending",
                }
            )
            try:
                response = requests.post(
                    comments_route(),
                    data=body,
                    headers=auth_headers(self.token),
                )
                response = response.json()
            except Exception as e:
                raise EJCommunicationError
            return response

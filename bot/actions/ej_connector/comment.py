from .routes import auth_headers
import json
import requests
from .constants import *
import logging

logger = logging.getLogger(__name__)


class Comment:
    """Comment controls commenting requests to EJ API and some validations during bot execution."""

    def __init__(self, conversation_id: str, comment_text: str, token: str):
        self.conversation_id = conversation_id
        self.text = comment_text
        self.token = token

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

    @staticmethod
    def pause_to_ask_comment():
        return {"vote": "pausa para pedir comentario"}

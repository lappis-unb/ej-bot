from .conversation import Conversation
from .ej_api import EjApi
from .routes import board_url


class Board:

    def __init__(self, id, tracker):
        self.id = id
        self.conversations: Conversation = []
        self.ej_api = EjApi(tracker)
        self._set_board(tracker)

    def _set_board(self, tracker):
        response = self.ej_api.request(board_url(self.id))
        data = response.json()
        self.title = data.get("title")
        self.description = data.get("description")
        self.conversations = (
            [
                Conversation(tracker, **conversation)
                for conversation in data.get("conversations")
            ]
            if data.get("conversations")
            else []
        )

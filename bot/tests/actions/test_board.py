import pytest
from unittest.mock import MagicMock, patch
from ej.boards import Board
from ej.conversation import Conversation
from ej.ej_api import EjApi


class TestBoard:

    @patch("ej.boards.EjApi")
    def test_board_initialization(self, MockEjApi):
        tracker = MagicMock()
        mock_api_instance = MockEjApi.return_value
        mock_api_instance.request.return_value.json.return_value = {
            "title": "Test Board",
            "description": "Test Description",
            "conversations": [],
        }

        board = Board(1, tracker)

        assert board.id == 1
        assert board.title == "Test Board"
        assert board.description == "Test Description"
        assert isinstance(board.conversations, list)
        assert len(board.conversations) == 0

    @patch("ej.boards.EjApi")
    @patch("ej.boards.Conversation")
    def test_set_board(self, MockConversation, MockEjApi):
        tracker = MagicMock()
        mock_api_instance = MockEjApi.return_value
        mock_api_instance.request.return_value.json.return_value = {
            "title": "Test Board",
            "description": "Test Description",
            "conversations": [{"id": 1}, {"id": 2}],
        }

        board = Board(1, tracker)

        assert board.title == "Test Board"
        assert board.description == "Test Description"
        assert len(board.conversations) == 2
        MockConversation.assert_any_call(tracker, {"id": 1})
        MockConversation.assert_any_call(tracker, {"id": 2})

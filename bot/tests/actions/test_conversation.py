import unittest
from unittest.mock import Mock, patch
from ej.ej_api import EjApi
from rasa_sdk import Tracker
from ej.conversation import Conversation, EJCommunicationError


class TestConversation(unittest.TestCase):
    def setUp(self):
        self.tracker = Mock(spec=Tracker)
        self.extra_data = {
            "id": "123",
            "title": "Test Title",
            "participants_can_add_comments": True,
            "anonymous_votes_limit": 5,
        }
        self.conversation = Conversation(self.tracker, self.extra_data)

    def test_init(self):
        self.assertEqual(self.conversation.id, "123")
        self.assertEqual(self.conversation.title, "Test Title")
        self.assertTrue(self.conversation.participant_can_add_comments)
        self.assertEqual(self.conversation.anonymous_votes_limit, 5)
        self.assertIsInstance(self.conversation.ej_api, EjApi)

    @patch.object(EjApi, "request")
    def test_get_participant_statistics(self, mock_request):
        mock_response = Mock()
        mock_response.json.return_value = {"data": "test"}
        mock_request.return_value = mock_response

        result = self.conversation.get_participant_statistics()
        self.assertEqual(result, {"data": "test"})

        mock_request.side_effect = Exception
        with self.assertRaises(EJCommunicationError):
            self.conversation.get_participant_statistics()

    @patch.object(EjApi, "request")
    def test_get_next_comment(self, mock_request):
        mock_response = Mock()
        mock_response.json.return_value = {
            "links": {"self": "http://example.com/comments/456/"},
            "data": "test",
        }
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        result = self.conversation.get_next_comment()
        self.assertEqual(result["id"], "456")
        self.assertEqual(result["data"], "test")

        mock_response.status_code = 500
        mock_request.return_value = mock_response
        with self.assertRaises(EJCommunicationError):
            self.conversation.get_next_comment()

    def test_user_should_authenticate(self):
        statistics = {"comments": 5}
        self.assertTrue(Conversation.user_should_authenticate(False, 5, statistics))
        self.assertFalse(Conversation.user_should_authenticate(True, 5, statistics))

    def test_available_comments_to_vote(self):
        statistics = {"missing_votes": 1}
        self.assertTrue(Conversation.available_comments_to_vote(statistics))
        statistics = {"missing_votes": 0}
        self.assertFalse(Conversation.available_comments_to_vote(statistics))

    def test_get_total_comments(self):
        statistics = {"total_comments": 10}
        self.assertEqual(Conversation.get_total_comments(statistics), 10)

    def test_get_user_voted_comments_counter(self):
        statistics = {"comments": 5}
        self.assertEqual(Conversation.get_user_voted_comments_counter(statistics), 5)

    def test_user_can_add_comment(self):
        statistics = {"total_comments": 4, "comments": 4}
        self.tracker.get_slot.return_value = True
        self.assertTrue(Conversation.user_can_add_comment(statistics, self.tracker))

        statistics = {"total_comments": 3, "comments": 2}
        self.assertTrue(Conversation.user_can_add_comment(statistics, self.tracker))

        statistics = {"total_comments": 4, "comments": 3}
        self.assertFalse(Conversation.user_can_add_comment(statistics, self.tracker))

    def test_pause_to_ask_comment(self):
        self.assertTrue(
            Conversation.pause_to_ask_comment("PAUSA PARA PEDIR COMENTARIO")
        )
        self.assertFalse(Conversation.pause_to_ask_comment("OTHER VALUE"))


if __name__ == "__main__":
    unittest.main()

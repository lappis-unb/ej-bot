import unittest
from unittest.mock import MagicMock, patch
from bot.ej.ej_api import EjApi


class TestEjApi(unittest.TestCase):

    def setUp(self):
        self.tracker = MagicMock()
        self.tracker.get_slot.side_effect = lambda x: (
            "test_token" if x == "access_token" else "refresh_token"
        )
        self.ej_api = EjApi(tracker=self.tracker)

    def test_initialization(self):
        self.assertEqual(self.ej_api.access_token, "test_token")
        self.assertEqual(self.ej_api.refresh_token, "refresh_token")

    def test_get_headers_with_access_token(self):
        headers = self.ej_api.get_headers()
        self.assertIn("Authorization", headers)

    def test_get_headers_without_access_token(self):
        self.tracker.get_slot.side_effect = lambda x: None
        headers = self.ej_api.get_headers()
        self.assertNotIn("Authorization", headers)

    @patch("requests.post")
    def test_refresh_access_token_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"access": "new_access_token"}
        mock_post.return_value = mock_response

        self.ej_api._refresh_access_token()
        self.assertEqual(self.ej_api.access_token, "new_access_token")
        self.tracker.update_slots.assert_called_once_with(
            {"access_token": "new_access_token"}
        )

    @patch("requests.post")
    def test_refresh_access_token_failure(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_post.return_value = mock_response

        with self.assertRaises(Exception):
            self.ej_api._refresh_access_token()

    @patch("requests.post")
    def test_post_request(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        response = self.ej_api._post(
            "http://example.com",
            {"Authorization": "Bearer test_token"},
            {"key": "value"},
        )
        self.assertEqual(response.status_code, 200)

    @patch("requests.get")
    def test_get_request(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        response = self.ej_api._get(
            "http://example.com", {"Authorization": "Bearer test_token"}
        )
        self.assertEqual(response.status_code, 200)

    @patch("requests.post")
    @patch("requests.get")
    def test_request_with_payload(self, mock_get, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        response = self.ej_api.request("http://example.com", {"key": "value"})
        self.assertEqual(response.status_code, 200)

    @patch("requests.post")
    @patch("requests.get")
    def test_request_without_payload(self, mock_get, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        response = self.ej_api.request("http://example.com")
        self.assertEqual(response.status_code, 200)

    @patch("requests.post")
    @patch("requests.get")
    def test_request_with_token_refresh(self, mock_get, mock_post):
        mock_response_401 = MagicMock()
        mock_response_401.status_code = 401
        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_post.side_effect = [mock_response_401, mock_response_200]

        self.ej_api._refresh_access_token = MagicMock()

        response = self.ej_api.request("http://example.com", {"key": "value"})
        self.assertEqual(response.status_code, 200)
        self.ej_api._refresh_access_token.assert_called_once()


if __name__ == "__main__":
    unittest.main()

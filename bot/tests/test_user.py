import json
import unittest

from bot.actions.ej_connector.user import User


class UserTest(unittest.TestCase):
    def test_creating_user(self):
        user = User("1234", "David")
        assert user.name == "David"
        assert user.email == f"1234-opinion-bot@mail.com"

    def test_serializing_user(self):
        user = User("1234", "David")
        user_dict = user.serialize()
        assert json.loads(user_dict)["name"] == "David"

    def test_get_username_from_tracker(self):
        state = {
            "latest_message": {
                "metadata": {
                    "token": "",
                    "bot": False,
                    "channel_id": "PtSjgJqB29fcy9vFd",
                    "channel_name": "mr_davidCarlos-telegram",
                    "message_id": "f3yTeCyHAuPNDdQZv",
                    "timestamp": "2022-06-20T15:23:17.242Z",
                    "user_id": "9H7jF3P6PnStr496r",
                    "user_name": "mr_davidCarlos",
                    "text": "start 74",
                    "siteUrl": "http://localhost:3000",
                }
            }
        }
        username = User.get_name_from_tracker_state(state)
        assert username == "mr_davidCarlos"

    def test_get_anonymous_username_from_tracker(self):
        state = {"latest_message": {"metadata": {}}}
        username = User.get_name_from_tracker_state(state)
        assert username == User.ANONYMOUS_USER_NAME

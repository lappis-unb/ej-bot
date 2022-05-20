from actions.ej_connector.user import User
import json
import unittest


class UserTest(unittest.TestCase):
    def test_creating_user(self):
        user = User("1234", "David")
        assert user.name == "David"
        assert user.email == f"1234-rasa@mail.com"

    def test_serializing_user(self):
        user = User("1234", "David")
        user_dict = user.serialize()
        assert json.loads(user_dict)["name"] == "David"

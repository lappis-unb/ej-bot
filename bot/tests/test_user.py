from actions.ej_connector.user import User
import json
import unittest


class UserTest(unittest.TestCase):
    def test_creating_user(self):
        user = User("1234", "David", "61999999999")
        assert user.name == "David"
        assert user.phone_number == "61999999999"
        assert user.email == f"1234-rasa@mail.com"

    def test_serializing_user(self):
        user = User("1234", "David", "61999999999")
        user_dict = user.serialize()
        assert json.loads(user_dict)["name"] == "David"

    def test_format_user_phone_number(self):
        user = User("1234", "David", "(61)999999999")
        assert user.phone_number == "61999999999"
        user = User("1234", "David", "(61)98117-8174")
        assert user.phone_number == "61981178174"
        user = User("1234", "David", "6198117-8174")
        assert user.phone_number == "61981178174"

    def test_format_user_without_phone_number(self):
        user = User("1234", "David", "")
        assert user.phone_number == ""
        user = User("1234", "David", None)
        assert user.phone_number == ""

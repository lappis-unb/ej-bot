import json
import pytest

from bot.ej.user import User


class TestUser:
    def test_generate_password(self, tracker):
        user = User(tracker)
        user._set_password()
        assert user.password == user._get_password_hash()
        assert user.password_confirm == user._get_password_hash()

    def test_generate_password_raises_error(self, tracker):
        user = User(tracker)
        user.sender_id = None
        with pytest.raises(Exception):
            user._set_password()

    def test_creating_user(self, tracker):
        user = User(tracker)
        assert user.name == "mr_davidCarlos"
        assert user.email == f"1234-opinion-bot@mail.com"

    def test_serializing_user(self, tracker):
        user = User(tracker)
        user_dict = user.registration_data()
        assert json.loads(user_dict)["name"] == "mr_davidCarlos"

    def test_get_username_from_tracker_on_telegram_channel(self, tracker):
        user = User(tracker)
        assert user.name == "mr_davidCarlos"

    def test_get_anonymous_username_from_tracker(self, anonymous_tracker):
        user = User(anonymous_tracker)
        assert user.name == User.ANONYMOUS_USER_NAME

    def test_get_username_from_tracker_on_whatsapp_channel(self, wpp_tracker):
        user = User(wpp_tracker)
        assert user.name == "David Carlos"

import json
from bot.ej.settings import SECRET_KEY
import pytest

from bot.ej.user import User


class TestUser:
    def test_get_password_hash(self, tracker):
        import base64
        import hashlib

        user = User(tracker)

        # create a byte string for the password seed
        seed = f"{user.sender_id}{SECRET_KEY}".encode()

        # encode the seed using base64 lib
        seed_base64 = base64.b64encode(seed)

        # encrypt the base64 seed with sha256 algorithm
        password = hashlib.sha256(seed_base64).hexdigest()

        assert user._get_password() == password

    def test_generate_password(self, tracker):
        user = User(tracker)
        assert user.password == user._get_password()
        assert user.password_confirm == user._get_password()

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

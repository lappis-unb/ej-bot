from unittest.mock import Mock

import pytest


@pytest.fixture
def tracker():
    tracker = Mock()
    tracker.sender_id = "1234"
    tracker.get_slot = lambda x: "1234"
    tracker.get_latest_input_channel = lambda: "whatsapp"
    return tracker


@pytest.fixture
def metadata():
    return {"other_keys": " notlivechat"}


@pytest.fixture
def livechat_metadata():
    return {"agent": "livechat"}

from unittest.mock import Mock

import pytest


@pytest.fixture
def tracker():
    slots = {
        "has_completed_registration": False,
        "participant_can_add_comments": False,
        "access_token": "1234",
        "refresh_token": "5678",
    }
    tracker = Mock()
    tracker.sender_id = "1234"
    tracker.get_slot = lambda x: "1234"
    tracker.get_latest_input_channel = lambda: "whatsapp"
    tracker.get_slot = lambda slot: slots[slot]
    return tracker


@pytest.fixture
def metadata():
    return {"other_keys": " notlivechat"}


@pytest.fixture
def livechat_metadata():
    return {"agent": "livechat"}

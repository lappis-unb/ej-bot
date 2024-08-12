from unittest.mock import Mock

import pytest

from bot.ej.conversation import Conversation


@pytest.fixture
def conversation_statistics():
    return {
        "votes": 0,
        "missing_votes": 10,
        "participation_ratio": 0.0,
        "total_comments": 20,
        "comments": 0,
    }


@pytest.fixture
def dispatcher():
    dispatcher = Mock()
    dispatcher.utter_message = lambda **kwargs: "some_utter"
    return dispatcher


@pytest.fixture
def tracker():
    slots = {
        "has_completed_registration": False,
        "participant_can_add_comments": False,
        "anonymous_votes_limit": 10,
        "access_token": "1234",
        "refresh_token": "5678",
        "conversation_id": "1",
        "conversation_id_cache": "1",
        "conversation_title": "conversation title",
    }

    def set_slot(slot, value):
        slots[slot] = value

    tracker = Mock()
    tracker.sender_id = "1234"
    tracker.conversation_statistics = "1234"
    tracker.get_slot = lambda x: "1234"
    tracker.get_latest_input_channel = lambda: "whatsapp"
    tracker.latest_message = {
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
    tracker.get_slot = lambda slot: slots[slot]
    tracker.set_slot = set_slot
    return tracker


@pytest.fixture
def telegram_tracker(tracker):
    tracker.latest_message = {
        "metadata": {
            "token": "",
            "bot": False,
            "channel_id": "PtSjgJqB29fcy9vFd",
            "channel_name": "mr_davidCarlos-telegram",
            "message_id": "f3yTeCyHAuPNDdQZv",
            "timestamp": "2022-06-20T15:23:17.242Z",
            "user_id": "9H7jF3P6PnStr496r",
            "contact_name": "David Carlos",
            "text": "start 74",
            "siteUrl": "http://localhost:3000",
        }
    }
    return tracker


@pytest.fixture
def anonymous_tracker(tracker):
    tracker.latest_message = {"metadata": {}}
    return tracker


@pytest.fixture
def wpp_tracker(tracker):
    tracker.latest_message = {
        "metadata": {
            "token": "",
            "bot": False,
            "channel_id": "PtSjgJqB29fcy9vFd",
            "channel_name": "mr_davidCarlos-telegram",
            "message_id": "f3yTeCyHAuPNDdQZv",
            "timestamp": "2022-06-20T15:23:17.242Z",
            "user_id": "9H7jF3P6PnStr496r",
            "contact_name": "David Carlos",
            "text": "start 74",
            "siteUrl": "http://localhost:3000",
        }
    }
    return tracker


@pytest.fixture
def comment():
    return {"content": "new comment", "id": "1"}


@pytest.fixture
def conversation(tracker, comment):
    conversation = Conversation(tracker)
    conversation.get_next_comment = Mock()
    conversation.get_next_comment = lambda: comment
    return conversation


@pytest.fixture
def metadata():
    return {"other_keys": " notlivechat"}


@pytest.fixture
def livechat_metadata():
    return {"agent": "livechat"}

from .ej_connector import API


def get_comment_utter(metadata, comment_title):
    if metadata and "agent" in metadata:
        return get_livechat_utter(comment_title)
    return get_buttons_utter(comment_title)


def get_buttons_utter(comment_title):
    buttons = [
        {"title": "Concordar", "payload": "Concordar"},
        {"title": "Discordar", "payload": "Discordar"},
        {"title": "Pular", "payload": "Pular"},
    ]
    return {"text": comment_title, "buttons": buttons}


def get_livechat_utter(comment_title):
    # channel is livechat, can't render buttons
    return {"text": comment_title}


def is_socketio_rasax_channel(tracker):
    """Rasa X is simulating a Webchat conversation."""
    return tracker.get_latest_input_channel() == "rasa" and tracker.get_slot("url")


def is_telegram_rasax_channel(tracker):
    """Rasa X is simulating a Webchat conversation."""
    tracker.get_latest_input_channel() == "rasa" and not tracker.get_slot("url")

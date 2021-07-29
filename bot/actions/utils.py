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


def authenticate_user(user_phone_number, last_intent, current_rasa_conversation_id):
    """
    Differentiate user type of login (using phone number or anonymous)
    providing the current flow for conversation
    """
    if user_phone_number and last_intent == "phone_number":
        user = API.get_or_create_user(
            current_rasa_conversation_id, user_phone_number, user_phone_number
        )
        utter_name = "utter_got_phone_number"
    else:
        user = API.get_or_create_user(current_rasa_conversation_id)
        utter_name = "utter_user_want_anonymous"

    return {"user": user, "utter_name": utter_name}

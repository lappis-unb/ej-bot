from .ej_connector import API

VOTE_VALUES = ["Concordar", "Discordar", "Pular", "1", "-1", "0"]


def define_vote_utter(metadata, message):
    if "agent" in metadata:
        # channel is livechat, can't render buttons
        message = {"text": message}
    else:
        buttons = [
            {"title": "Concordar", "payload": "Concordar"},
            {"title": "Discordar", "payload": "Discordar"},
            {"title": "Pular", "payload": "Pular"},
        ]
        message = {"text": message, "buttons": buttons}
    return message


def authenticate_user(user_email, last_intent, current_rasa_conversation_id):
    """
    Differentiate user type of login (using email or anonymous)
    providing the current flow for conversation
    """
    if user_email and last_intent == "email":
        user = API.get_or_create_user(
            current_rasa_conversation_id, user_email, user_email
        )
        utter_name = "utter_got_email"
    else:
        user = API.get_or_create_user(current_rasa_conversation_id)
        utter_name = "utter_user_want_anonymous"

    return {"user": user, "utter_name": utter_name}

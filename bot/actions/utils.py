# from .ej_connector import API


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


def remove_special(line):
    for char in ":+":
        line = line.replace(char, "")
    return line

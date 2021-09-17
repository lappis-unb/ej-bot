def remove_special(line):
    for char in ":+":
        line = line.replace(char, "")
    return line


def number_from_wpp(str_num):
    num = ""
    for c in str_num:
        if c.isnumeric():
            num = num + c
    return num


def get_comment_utter(metadata, comment_title, channel):
    if metadata and "agent" in metadata:
        return get_livechat_utter(comment_title)
    elif channel == "twilio":
        return comment_title + WHATSAPP_VT
    return get_buttons_utter(comment_title)


WHATSAPP_VT = "\n\n1. Concordar\n-1. Discordar\n0. Pular"


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

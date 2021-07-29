import os
import json


class User(object):
    """
    For telegram channel, tracker_sender_id is the unique ID from the user talking with the bot.
    """

    def __init__(self, tracker_sender_id, name="", phone_number=""):
        self.name = name
        self.display_name = ""
        self.phone_number = phone_number
        self.email = f"{tracker_sender_id}-rasa@mail.com"
        self.password = f"{tracker_sender_id}-rasa"
        self.password_confirm = f"{tracker_sender_id}-rasa"

    def serialize(self):
        return json.dumps(self.__dict__)

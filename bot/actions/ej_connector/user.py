import os
import json
import jwt


class User(object):
    def __init__(self, rasa_id, name="", phone_number=""):
        self.name = name
        self.display_name = ""
        secret = os.getenv("JWT_SECRET")
        encoded_id = jwt.encode({"rasa_id": rasa_id}, secret, algorithm="HS256")
        self.stats = {}

        if phone_number:
            self.phone_number = phone_number
            self.email = f"{phone_number}-rasa@mail.com"
            self.password = f"{encoded_id}-rasa"
            self.password_confirm = f"{encoded_id}-rasa"
        else:
            self.email = f"{encoded_id}-rasa@mail.com"
            self.password = f"{encoded_id}-rasa"
            self.password_confirm = f"{encoded_id}-rasa"

    def serialize(self):
        return json.dumps(self.__dict__)

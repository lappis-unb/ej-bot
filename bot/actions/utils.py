from .ej_connector import API


class VotingService:

    VALID_VOTE_VALUES = ["Concordar", "Discordar", "Pular", "1", "-1", "0"]

    def __init__(self, vote_slot_value, token):
        self.vote_slot_value = vote_slot_value
        self.token = token

    def stop_participation(self):
        return str(self.vote_slot_value).upper() == "PARAR"

    def vote_is_valid(self):
        return str(self.vote_slot_value) in VotingService.VALID_VOTE_VALUES

    def changes_current_participation_link(self):
        return self.vote_slot_value == "novo link de participação"

    def new_vote(self, comment_id):
        return API.send_comment_vote(comment_id, self.vote_slot_value, self.token)

    @staticmethod
    def intent_starts_new_conversation(current_intent):
        return current_intent == "start_with_conversation_id"

    @staticmethod
    def continue_voting():
        """
        Rasa end a form when all slots are filled. This method
        fill vote slot with None value, forcing the form to keep sending comments to user voting.
        """
        return {"vote": None}

    @staticmethod
    def stop_voting():
        """
        Rasa end a form when all slots are filled. This method
        fill vote slot with "parar" value, forcing the form to stop.

        On ActionFollowUpForm class, whe check if vote is == parar, if so,
        we send a utter finishing the conversation.
        """
        return {"vote": "parar"}

    def finished_voting(self):
        return {"vote": str(self.vote_slot_value).lower()}

    @staticmethod
    def new_participation_link():
        """
        Rasa end a form when all slots are filled. This method
        fill vote slot with "novo link de participação" value, forcing the form to stop.
        On ActionFollowUpForm class, whe check if vote is == novo link de participação, if so,
        we restart the story with the new conversation_id.

        This is necessary on the cenario where user is participating on a conversation,
        not vote on all comments, and then click on a new participation link. We need to
        stop the form, restarting the story from the begining.
        """
        return {"vote": "novo link de participação"}


class ConversationService:
    def __init__(self, conversation_id, token):
        self.conversation_id = conversation_id
        self.token = token

    def _set_statistics(self):
        self.statistics = API.get_user_conversation_statistics(
            self.conversation_id, self.token
        )

    def user_have_comments_to_vote(self):
        self._set_statistics()
        return self.statistics["missing_votes"] > 0


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

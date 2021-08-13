from .api import API


class VotingHelper:

    VALID_VOTE_VALUES = ["Concordar", "Discordar", "Pular", "1", "-1", "0"]

    def __init__(self, vote_slot_value, tracker):
        self.vote_slot_value = vote_slot_value
        self.channel = tracker.get_latest_input_channel()
        self.token = tracker.get_slot("ej_user_token")

    def vote_is_valid(self):
        return str(self.vote_slot_value) in VotingHelper.VALID_VOTE_VALUES

    def new_vote(self, comment_id):
        return API.send_comment_vote(
            comment_id, self.vote_slot_value, self.channel, self.token
        )

    def user_enters_a_new_comment(self):
        slot_value = str(self.vote_slot_value)
        return slot_value not in VotingHelper.VALID_VOTE_VALUES and slot_value[2] != "/"

    def send_new_comment(self, conversation_id):
        return API.send_new_comment(conversation_id, self.vote_slot_value, self.token)

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

    @staticmethod
    def pause_voting_to_ask_phone_number():
        """
        Rasa end a form when all slots are filled. This method
        fill vote slot with "parar" value, forcing the form to stop.

        On ActionFollowUpForm class, whe check if vote is == PAUSAR PARA PEDIR TELEFONE, if so,
        we send a utter finishing the conversation.
        """
        return {"vote": "pausar para pedir telefone"}

    @staticmethod
    def pause_voting_to_ask_engaging():
        """
        Rasa end a form when all slots are filled. This method
        fill vote slot with "parar" value, forcing the form to stop.

        On ActionFollowUpForm class, whe check if vote is == PAUSAR PARA ENGAJAR, if so,
        we send a utter finishing the conversation.
        """
        return {"vote": "pausar para engajar"}

    def finished_voting(self):
        return {"vote": str(self.vote_slot_value).lower()}


class EngageFactory:

    ENGAGE_LINKS = {
        "DudaDavidBot": "https://t.me/joinchat/rW8Tblsmxk83ZDMx",
        "BocaDeLoboBot": "https://t.me/abocadelobooficial",
    }

    @staticmethod
    def bot_has_engage_link(bot_name):
        return EngageFactory.ENGAGE_LINKS.get(bot_name)

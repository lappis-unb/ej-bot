from .api import API
from .helpers import EngageFactory


class ConversationController:
    def __init__(self, conversation_id, token):
        self.conversation_id = conversation_id
        self.token = token
        self.api = ConversationAPI(conversation_id, token)

    def user_have_comments_to_vote(self):
        statistics = self.api.get_participant_statistics()
        return statistics["missing_votes"] > 0

    @staticmethod
    def starts_conversation_from_another_link():
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

    @staticmethod
    def intent_starts_new_conversation(current_intent):
        return current_intent == "start_with_conversation_id"

    @staticmethod
    def is_vote_on_new_conversation(vote_slot_value):
        return vote_slot_value == "novo link de participação"

    @staticmethod
    def stop_participation(vote_slot_value):
        return str(vote_slot_value).upper() == "PARAR"

    @staticmethod
    def pause_to_ask_phone_number(vote_slot_value):
        return str(vote_slot_value).upper() == "PAUSAR PARA PEDIR TELEFONE"

    @staticmethod
    def pause_to_allow_engagement(vote_slot_value):
        return str(vote_slot_value).upper() == "PAUSAR PARA ENGAJAR"

    @staticmethod
    def dispatch_errors(dispatcher, FollowupAction):
        dispatcher.utter_message(template="utter_ej_communication_error")
        dispatcher.utter_message(template="utter_error_try_again_later")
        return [FollowupAction("action_session_start")]

    def time_to_ask_phone_number_again(self, participant_phone_number, statistics):
        total_comments = self.api.get_total_comments(statistics)
        voted_comments = self.api.get_voted_comments(statistics)
        if voted_comments == 0:
            return False
        participation_tax = total_comments / voted_comments
        return participation_tax == 2 and participant_phone_number == None

    def time_to_invite_to_engage(self, statistics, bot_name, telegram_engagement_group):
        voted_comments = self.api.get_voted_comments(statistics)
        if voted_comments == 0:
            return False
        engage_link = EngageFactory.bot_has_engage_link(bot_name)
        return engage_link and voted_comments == 3 and not telegram_engagement_group


class ConversationAPI:
    def __init__(self, conversation_id, token):
        self.conversation_id = conversation_id
        self.token = token

    def get_participant_statistics(self):
        return API.get_user_conversation_statistics(self.conversation_id, self.token)

    def get_next_comment(self):
        return API.get_next_comment(self.conversation_id, self.token)

    def get_total_comments(self, statistics):
        return statistics["missing_votes"] + statistics["votes"]

    def get_voted_comments(self, statistics):
        return statistics["votes"]

    def get_comment_title(self, comment, voted_comments, total_comments):
        return f"{comment['content']} \n O que você acha disso ({voted_comments}/{total_comments})?"

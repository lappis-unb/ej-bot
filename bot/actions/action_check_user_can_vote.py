from typing import Any, Dict, List, Text
from actions.logger import custom_logger
from rasa_sdk import Action, Tracker
from rasa_sdk.events import EventType, FollowupAction, SlotSet
from rasa_sdk.executor import CollectingDispatcher

from .ej_connector import EJCommunicationError, User
from .ej_connector.conversation import Conversation
from .ej_connector.constants import CONVERSATION_ID


class CheckUserCanVote(Action):
    """
    Esta ação verifica se um usuário pode votar em uma conversa específica.
    Ela avalia se o usuário é um bot e se o número de votos anônimos excede o número de comentários votados pelo usuário.
    """

    def __init__(self):
        self.total_comments = 0
        self.user_voted_comments = 0
        self.total_anonymous_votes = 0
        self.user_is_anonymous = True

    def name(self) -> Text:
        """
        Retorna o nome da ação.
        """
        return "action_check_user_can_vote"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        """
        Executa a ação de verificar se o usuário pode votar.
        """
        custom_logger("Running action_check_user_can_vote")

        conversation_id = CONVERSATION_ID
        custom_logger(f"conversation_id: {conversation_id}")

        conversation = Conversation(conversation_id, tracker)
        conversation_statistics = conversation.get_participant_statistics()

        if conversation_statistics.status_code != 200:
            return self._dispatch_errors(dispatcher)

        conversation_statistics = conversation_statistics.json()

        user = User(tracker)
        tracker_auth = user.authenticate()

        self._set_attributes(conversation_statistics, tracker_auth)

        custom_logger(f"self.total_comments: {self.total_comments}")
        custom_logger(f"self.user_voted_comments: {self.user_voted_comments}")
        custom_logger(f"self.total_anonymous_votes: {self.total_anonymous_votes}")
        custom_logger(f"self.user_is_anonymous: {self.user_is_anonymous}")

        try:
            user_can_vote = self._check_user_can_vote()

            custom_logger(f"User can vote: {user_can_vote}")

            return [SlotSet("user_can_vote", user_can_vote)]
        except EJCommunicationError:
            return self._dispatch_errors(dispatcher)

    def _set_attributes(self, conversation_statistics, tracker_auth):
        """
        Define os atributos da classe com base nas estatísticas da conversa.
        """
        self.total_comments = Conversation.get_total_comments(conversation_statistics)
        self.user_voted_comments = Conversation.get_user_voted_comments_counter(
            conversation_statistics
        )
        self.total_anonymous_votes = Conversation.get_total_anonymous_votes(
            conversation_statistics
        )
        self.user_is_anonymous = tracker_auth.get_slot("user_is_anonymous")

    def _dispatch_errors(self, dispatcher):
        """
        Envia mensagens de erro ao usuário.
        """
        dispatcher.utter_message(response="utter_ej_communication_error")
        dispatcher.utter_message(response="utter_error_try_again_later")
        return [FollowupAction("action_session_start")]

    def _check_user_can_vote(self) -> bool:
        """
        Verifica se o usuário pode votar com base nas regras definidas.
        """
        return (
            not self.user_is_anonymous
            or self.user_voted_comments < self.total_anonymous_votes
        )

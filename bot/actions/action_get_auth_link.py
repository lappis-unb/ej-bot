from typing import List, Dict, Text
from rasa_sdk import Action, Tracker
from rasa_sdk.events import EventType, SlotSet
from rasa_sdk.executor import CollectingDispatcher
from datetime import timedelta

from .ej_connector import EJCommunicationError, User

AUTHENTICATION_URL = "https://brasilparticipativo.presidencia.gov.br/users/sign_in"
TOKEN_EXPIRATION_TIME = timedelta(minutes=10)


class ActionAuthLink(Action):
    """
    Esta ação gera um link de autenticação para o usuário, permitindo que ele se autentique
    para continuar a interação. O link é gerado com um token de acesso temporário.
    """

    def name(self) -> Text:
        """
        Retorna o nome da ação.
        """
        return "action_get_auth_link"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        """
        Executa a ação de gerar o link de autenticação e o envia ao usuário.
        """
        try:
            auth_link = self._get_authenticate_link(
                tracker.sender_id, tracker.get_slot("secret_id")
            )

            return [SlotSet("auth_link", auth_link)]
        except EJCommunicationError:
            dispatcher.utter_message(response="utter_ej_communication_error")
            dispatcher.utter_message(response="utter_error_try_again_later")
            return []

    def _get_authenticate_link(self, user_id: Text, secret_id: Text) -> Text:
        """
        Gera o link de autenticação com base no ID do usuário e no ID secreto.
        """
        authentication_token = User.generate_access_token(
            user_id, secret_id, TOKEN_EXPIRATION_TIME.total_seconds()
        )
        auth_link = f"{AUTHENTICATION_URL}?token={authentication_token}"
        return auth_link

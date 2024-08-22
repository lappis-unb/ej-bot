import os

HEADERS = {
    "Content-Type": "application/json",
}
VALID_VOTE_VALUES = ["1", "-1", "0"]
START_CONVERSATION_COMMAND = "/start"

HOST = os.getenv("EJ_HOST")
API_URL = f"{HOST}/api/v1"
CONVERSATIONS_URL = (
    f"{API_URL}/conversations/?is_promoted=true&participation_source=bot"
)
REGISTRATION_URL = f"{API_URL}/users/"
AUTH_URL = f"{API_URL}/token/"
REFRESH_TOKEN_URL = f"{API_URL}/refresh-token/"
VOTES_URL = f"{API_URL}/votes/"
COMMENTS_URL = f"{API_URL}/comments/"
PROFILE = f"{API_URL}/profiles/me/"


class EJCommunicationError(Exception):
    """Raised when request from EJ doesnt supply waited response"""

    def __init_(self, expression, message):
        self.expression = expression
        self.message = "Não consegui conectar na EJ"

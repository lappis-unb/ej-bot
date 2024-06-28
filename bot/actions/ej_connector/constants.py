import os

HEADERS = {
    "Content-Type": "application/json",
}
VALID_VOTE_VALUES = ["1", "-1", "0"]

HOST = os.getenv("EJ_HOST")
API_URL = f"{HOST}/api/v1"
CONVERSATIONS_URL = (
    f"{API_URL}/conversations/?is_promoted=true&participation_source=bot"
)
REGISTRATION_URL = f"{API_URL}/users/"
GET_USER_URL = f"{API_URL}/users/user/"
AUTH_URL = f"{API_URL}/token/"
REFRESH_TOKEN_URL = f"{API_URL}/refresh-token/"
VOTES_URL = f"{API_URL}/votes/"
COMMENTS_URL = f"{API_URL}/comments/"
CONVERSATION_ID = 1


class EJCommunicationError(Exception):
    """Raised when request from EJ doesnt supply waited response"""

    pass

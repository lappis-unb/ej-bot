import os

HEADERS = {
    "Content-Type": "application/json",
}
VOTE_CHOICES = {"Pular": 0, "Concordar": 1, "Discordar": -1}
HOST = os.getenv("EJ_HOST")
API_URL = f"{HOST}/api/v1"
CONVERSATIONS_URL = (
    f"{API_URL}/conversations/?is_promoted=true&participation_source=bot"
)
REGISTRATION_URL = f"{HOST}/rest-auth/registration/"
PHONE_NUMBER_URL = f"{API_URL}/profiles/phone-number/"
VOTES_URL = f"{API_URL}/votes/"
COMMENTS_URL = f"{API_URL}/comments/"
MENSSAGE_CHANNELS = {"telegram": "telegram", "whatsapp": "twilio"}


class EJCommunicationError(Exception):
    """Raised when request from EJ doesnt supply waited response"""

    pass

from datetime import timedelta
import os

from dotenv import load_dotenv

load_dotenv()

HEADERS = {
    "Content-Type": "application/json",
}
HOST = os.getenv("EJ_HOST")
API_URL = f"{HOST}/api/v1"
TOKEN_EXPIRATION_TIME = timedelta(minutes=10)
JWT_SECRET = os.getenv("JWT_SECRET")
SECRET_KEY = os.getenv("SECRET_KEY")
EXTERNAL_AUTHENTICATION_HOST = os.getenv("EXTERNAL_AUTHENTICATION_HOST", "")
BP_EJ_COMPONENT_ID = os.getenv("BP_EJ_COMPONENT_ID", "")
BOARD_ID = os.getenv("BOARD_ID", None)
CONVERSATION_ID = os.getenv("CONVERSATION_ID", None)


class EJCommunicationError(Exception):
    """Raised when request from EJ doesnt supply waited response"""

    def __init_(self, expression, message):
        self.expression = expression
        self.message = "Não consegui conectar na EJ"

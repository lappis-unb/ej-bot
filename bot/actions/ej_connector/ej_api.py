from dataclasses import dataclass
from typing import Any, Dict

import requests

from actions.logger import custom_logger
from rasa_sdk import Tracker

from .constants import REFRESH_TOKEN_URL, HEADERS
from .user import User
from .ej_error import EJError


@dataclass
class EjApi:
    """
    EjApi manages the requests sent to the EJ API. It also renew the access token when necessary.
    """

    def __init__(self, tracker: Tracker):
        self.tracker = tracker
        self.access_token = tracker.get_slot("access_token")
        self.refresh_token = tracker.get_slot("refresh_token")

    def _get_headers(self):
        headers = HEADERS.copy()
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def _refresh_access_token(self):
        """
        Requests a new access_token using the refresh_token attribute.
        """
        custom_logger("Refreshing access token.")

        payload = {"refresh": self.refresh_token}

        headers = self._get_headers()

        response = self._post(REFRESH_TOKEN_URL, headers, payload)
        if response.status_code == 200:
            data = response.json()
            self.access_token = data.get("access")
            self.tracker.slots["access_token"] = self.access_token
        elif response.status_code == 401:
            self._get_news_tokens()
        else:
            raise EJError(response.status_code)

    def _post(self, url: str, headers: Dict, payload=None):
        return requests.post(
            url,
            payload,
            headers=headers,
        )

    def _get(self, url: str, headers: Dict):
        return requests.get(url, headers=headers)

    def _get_news_tokens(self):
        user = User(self.tracker)
        tracker_auth = user.authenticate()
        self.tracker = tracker_auth
        self.access_token = self.tracker.get_slot("access_token")
        self.refresh_token = self.tracker.get_slot("refresh_token")

    def request(self, url: str, payload=None):
        """
        Send a HTTP request to the EJ API endpoints.
        """
        headers = self._get_headers()
        response = None

        if payload:
            response = self._post(url, headers, payload)
        else:
            response = self._get(url, headers)

        if response.status_code == 401:
            self._refresh_access_token()
            headers = self._get_headers()

            if payload:
                response = self._post(url, headers, payload)
            else:
                response = self._get(url, headers)

        return response

from dataclasses import dataclass
from typing import Any, Dict

import requests

from rasa_sdk import Tracker

from .constants import REFRESH_TOKEN_URL
from .routes import HEADERS, auth_headers


@dataclass
class EjApi:
    """
    EjApi manages the requests sent to the EJ API. It also renew the access token when necessary.
    """

    tracker: Tracker
    url: str = ""
    access_token: str = ""
    refresh_token: str = ""

    def __post_init__(self):
        if self.tracker:
            self.access_token = self.tracker.get_slot("access_token")
            self.refresh_token = self.tracker.get_slot("refresh_token")

    def get_headers(self):
        """
        Returns the headers for the HTTP request. If tracker access_token is available, includes
        it with an authorization header.
        """
        if self.tracker:
            access_token = self.tracker.get_slot("access_token")
            if access_token:
                return auth_headers(access_token)
        return HEADERS

    def _refresh_access_token(self):
        """
        Requests a new access_token using the refresh_token attribute.
        """
        response = requests.post(REFRESH_TOKEN_URL, {"refresh": self.refresh_token})
        if response.status_code == 200:
            data = response.json()
            self.access_token = data.get("access")
            self.tracker.slots["access_token"] = self.access_token
        else:
            raise Exception("could not refresh access token on EJ API.")

    def _post(self, url: str, headers: Dict, payload=None):
        return requests.post(
            url,
            payload,
            headers=headers,
        )

    def _put(self, url: str, headers: Dict, payload=None):
        return requests.put(
            url,
            payload,
            headers=headers,
        )

    def _get(self, url: str, headers: Dict):
        return requests.get(url, headers=headers)

    def request(self, url: str, payload=None, put=False):
        """
        Send a HTTP request to the EJ API endpoints.
        """
        response: Any
        headers = self.get_headers()
        if payload and not put:
            response = self._post(url, headers, payload)
            if response.status_code == 401:
                self._refresh_access_token()
                headers = self.get_headers()
                response = self._post(url, headers, payload)
        elif payload and put:
            response = self._put(url, headers, payload)
            if response.status_code == 401:
                self._refresh_access_token()
                headers = self.get_headers()
                response = self._put(url, headers, payload)
        else:
            response = self._get(url, headers)
            if response.status_code == 401:
                self._refresh_access_token()
                headers = self.get_headers()
                response = self._get(url, headers)
        return response

import os

HOST = os.getenv("EJ_HOST")
API_URL = f"{HOST}/api/v1"
HEADERS = {
    "Content-Type": "application/json",
}


def auth_headers(token):
    headers = HEADERS.copy()
    headers["Authorization"] = f"Token {token}"
    return headers


def conversation_url(conversation_id):
    return f"{API_URL}/conversations/{conversation_id}/"


def conversation_random_comment_url(conversation_id):
    return f"{conversation_url(conversation_id)}random-comment/"


def user_statistics_url(conversation_id):
    return f"{conversation_url(conversation_id)}user-statistics/"


def user_comments_route(conversation_id):
    return f"{conversation_url(conversation_id)}user-comments/"


def user_pending_comments_route(conversation_id):
    return f"{conversation_url(conversation_id)}user-pending-comments/"


def webchat_domain_url(url):
    return f"{API_URL}/rasa-conversations/integrations?domain={url}"

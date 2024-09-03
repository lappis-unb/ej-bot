from .settings import API_URL, HEADERS

HEADERS = {
    "Content-Type": "application/json",
}


def auth_headers(token):
    headers = HEADERS.copy()
    headers["Authorization"] = f"Bearer {token}"
    return headers


def board_route(board_id):
    return f"{API_URL}/boards/{board_id}/"


def conversation_route(conversation_id):
    return f"{API_URL}/conversations/{conversation_id}/"


def random_comment_route(conversation_id):
    return f"{conversation_route(conversation_id)}random-comment/"


def user_statistics_route(conversation_id):
    return f"{conversation_route(conversation_id)}user-statistics/"


def user_comments_route(conversation_id):
    return f"{conversation_route(conversation_id)}user-comments/"


def user_pending_comments_route(conversation_id):
    return f"{conversation_route(conversation_id)}user-pending-comments/"


def auth_route():
    return f"{API_URL}/token/"


def registration_route():
    return f"{API_URL}/users/"


def refresh_token_route():
    return f"{API_URL}/refresh-token/"


def votes_route():
    return f"{API_URL}/votes/"


def comments_route():
    return f"{API_URL}/comments/"


def my_profile_route():
    return f"{API_URL}/profiles/me/"


def profiles_route():
    return f"{API_URL}/profiles/"

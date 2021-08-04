from actions.ej_connector.helpers import VotingHelper
from actions.ej_connector.conversation import ConversationController
from actions.utils import *
import unittest.mock as mock


def test_vote_values_list():
    values = ["Concordar", "Discordar", "Pular", "1", "-1", "0"]
    assert values == VotingHelper.VALID_VOTE_VALUES


def test_stop_participation():
    assert ConversationController.stop_participation("parar") == True


def test_vote_is_valid():
    voting_helper = VotingHelper("Concordar", "")
    assert voting_helper.vote_is_valid() == True


def test_vote_is_invalid():
    voting_helper = VotingHelper("xpto", "")
    assert voting_helper.vote_is_valid() == False


def test_user_clicked_new_participation_link():
    assert (
        ConversationController.intent_starts_new_conversation(
            "start_with_conversation_id"
        )
        == True
    )


def test_continue_voting():
    assert VotingHelper.continue_voting() == {"vote": None}


def test_stop_voting():
    assert VotingHelper.stop_voting() == {"vote": "parar"}


def test_finished_voting():
    voting_helper = VotingHelper("Discordar", "")
    assert voting_helper.finished_voting() == {"vote": "discordar"}


def test_user_have_comments_to_vote():
    conversation_controller = ConversationController("1234", "")
    conversation_controller.api.get_participant_statistics = mock.MagicMock(
        return_value={"missing_votes": 5}
    )
    assert conversation_controller.user_have_comments_to_vote() == True


def test_define_vote_livechat():
    metadata = {"agent": "livechat"}
    message = "vote message"
    utter = get_comment_utter(metadata, message)

    assert not "buttons" in utter
    assert "text" in utter
    assert message == utter["text"]


def test_define_vote_channel_not_livechat():
    metadata = {"other_keys": " notlivechat"}
    message = "vote message"
    utter = get_comment_utter(metadata, message)

    assert "buttons" in utter
    assert "text" in utter
    assert message == utter["text"]

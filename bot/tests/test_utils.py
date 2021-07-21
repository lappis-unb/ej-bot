from actions.utils import VotingService, ConversationService, define_vote_utter
import mock


def test_vote_values_list():
    values = ["Concordar", "Discordar", "Pular", "1", "-1", "0"]
    assert values == VotingService.VALID_VOTE_VALUES


def test_stop_participation():
    voting_service = VotingService("parar", "")
    assert voting_service.stop_participation() == True


def test_vote_is_valid():
    voting_service = VotingService("Concordar", "")
    assert voting_service.vote_is_valid() == True


def test_is_invalid():
    voting_service = VotingService("xpto", "")
    assert voting_service.vote_is_valid() == False


def test_user_clicked_new_participation_link():
    assert (
        VotingService.intent_starts_new_conversation("start_with_conversation_id")
        == True
    )


def test_continue_voting():
    assert VotingService.continue_voting() == {"vote": None}


def test_stop_voting():
    assert VotingService.stop_voting() == {"vote": "parar"}


def test_finished_voting():
    voting_service = VotingService("Discordar", "")
    assert voting_service.finished_voting() == {"vote": "discordar"}


def test_user_have_comments_to_vote():
    conversation_service = ConversationService("1234", "")
    conversation_service._set_statistics = mock.MagicMock()
    conversation_service.statistics = {"missing_votes": 5}
    assert conversation_service.user_have_comments_to_vote() == True


def test_define_vote_livechat():
    metadata = {"agent": "livechat"}
    message = "vote message"
    returned_value = define_vote_utter(metadata, message)

    assert not "buttons" in returned_value
    assert "text" in returned_value
    assert message == returned_value["text"]


def test_define_vote_channel_not_livechat():
    metadata = {"other_keys": " notlivechat"}
    message = "vote message"
    returned_value = define_vote_utter(metadata, message)

    assert "buttons" in returned_value
    assert "text" in returned_value
    assert message == returned_value["text"]

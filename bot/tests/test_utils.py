from actions.ej_connector.helpers import VotingHelper
from actions.ej_connector.conversation import ConversationController
from actions.utils import *
import unittest.mock as mock
from test_ej_connector import MockedTracker
from unittest.mock import MagicMock, patch
import unittest


class UtilsTest(unittest.TestCase):
    def test_vote_values_list(self):
        values = ["Concordar", "Discordar", "Pular", "1", "0", "2"]
        assert values == VotingHelper.VALID_VOTE_VALUES

    def test_stop_participation(self):
        assert ConversationController.user_wants_to_stop_participation("parar") == True

    def test_vote_is_valid(self):
        mocked_tracker = MockedTracker()
        voting_helper = VotingHelper("Concordar", mocked_tracker)
        assert voting_helper.vote_is_valid() == True

    def test_vote_is_invalid(self):
        mocked_tracker = MockedTracker()
        voting_helper = VotingHelper("xpto", mocked_tracker)
        assert voting_helper.vote_is_valid() == False

    @patch("actions.ej_connector.api.requests.get")
    def test_user_clicked_new_participation_link(self, mock_get):
        # mock_get.return_value = {"missing_votes": 5}
        mocked_tracker = MockedTracker()
        mocked_tracker.latest_message = {
            "intent": {"name": "start_with_conversation_id"}
        }
        conversation_controller = ConversationController(mocked_tracker)
        conversation_controller.api.get_participant_statistics = MagicMock(
            return_value={"missing_votes": 5}
        )
        assert conversation_controller.intent_starts_new_conversation() == True

    def test_continue_voting(self):
        assert VotingHelper.continue_voting() == {"vote": None}

    def test_stop_voting(self):
        assert VotingHelper.stop_voting() == {"vote": "parar"}

    def test_finished_voting(self):
        mocked_tracker = MockedTracker()
        voting_helper = VotingHelper("Discordar", mocked_tracker)
        assert voting_helper.finished_voting() == {"vote": "discordar"}

    @patch("actions.ej_connector.api.requests.get")
    def test_user_have_comments_to_vote(self, mock_get):
        mocked_tracker = MockedTracker()
        conversation_controller = ConversationController(mocked_tracker)
        conversation_controller.api.get_participant_statistics = MagicMock(
            return_value={"missing_votes": 5}
        )
        assert conversation_controller.user_have_comments_to_vote() == True

    def test_define_vote_livechat(self):
        metadata = {"agent": "livechat"}
        message = "vote message"
        channel = "livechat"
        utter = get_comment_utter(metadata, message, channel)

        assert not "buttons" in utter
        assert "text" in utter
        assert message == utter["text"]

    def test_define_vote_channel_telegram(self):
        metadata = {"other_keys": " notlivechat"}
        message = "vote message"
        channel = "telegram"
        utter = get_comment_utter(metadata, message, channel)

        assert "buttons" in utter
        assert "text" in utter
        assert message == utter["text"]

    def test_define_vote_channel_whatsapp(self):
        metadata = {"other_keys": " notlivechat"}
        message = "vote message"
        channel = "twilio"
        utter = get_comment_utter(metadata, message, channel)

        assert "- Responda *1* para *concordar*" in utter
        assert "- Responda *2* para *discordar*" in utter
        assert "- Ou responda *0* para *pular* um comentário." in utter
        assert message in utter

    def test_remove_special(self):
        assert ":" not in remove_special("sdf:adsf")
        assert "+" not in remove_special("sdf+adsf")
        assert "+" not in remove_special("sdf+:adsf")
        assert ":" not in remove_special("sdf+:adsf")

    def test_number_from_wpp(self):
        example_num = "whatsapp:+14155888888"
        to_be_removed = "whatsapp:+"
        found = False
        formated_num = number_from_wpp(example_num)
        for r in to_be_removed:
            if r in formated_num:
                found = True
                assert found == False

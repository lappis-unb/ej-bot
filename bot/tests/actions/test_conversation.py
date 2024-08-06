from ej.conversation import Conversation


class TestConversation:
    def test_user_should_not_authenticate_during_conversation(self, tracker):
        conversation = Conversation(tracker)
        assert not conversation.user_should_authenticate(
            False, conversation.anonymous_votes_limit, {"comments": 4}
        )

    def test_user_should_authenticate_during_conversation(self, tracker):
        conversation = Conversation(tracker)
        assert conversation.user_should_authenticate(
            False, conversation.anonymous_votes_limit, {"comments": 10}
        )

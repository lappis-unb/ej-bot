import pytest
from unittest.mock import Mock, patch
from bot.ej.profile import (
    Profile,
    Question,
    Gender,
)


# Test initialization of the Profile object
def test_profile_initialization(mock_profile):
    assert isinstance(mock_profile.questions, list)
    assert isinstance(mock_profile.remaining_questions, list)


# Test retrieving the user profile from the API
def test_get_user_profile(mock_profile):
    assert mock_profile.user == 1
    assert mock_profile.gender == Gender.NOT_FILLED


# Test setting up the remaining questions based on the user profile
def test_set_remaining_questions(mock_profile):
    assert len(mock_profile.remaining_questions) > 0
    assert all(isinstance(q, Question) for q in mock_profile.remaining_questions)


# Test validation of a valid answer
@patch("bot.ej.ej_api.requests.post")
def test_is_valid_answer_valid(mock_post):
    mock_post.return_value = Mock(ok=True)
    mock_profile = Mock(spec=Profile)
    mock_profile.questions = [
        Question(
            id=1,
            body="What is your gender?",
            answers=[{"payload": 1, "title": "Female"}],
            change=Gender,
            put_payload="gender",
        )
    ]
    mock_profile.is_valid_answer.return_value = (True, None)

    is_valid, err = mock_profile.is_valid_answer(1, 1)
    assert is_valid is True
    assert err is None


# Test validation of an invalid answer
def test_is_valid_answer_invalid(mock_profile):
    mock_profile.questions = [
        Question(
            id=1,
            body="What is your gender?",
            answers=[{"payload": 1, "title": "Female"}],
            change=Gender,
            put_payload="gender",
        )
    ]
    is_valid, err = mock_profile.is_valid_answer(2, 1)
    assert is_valid is False
    assert err is None


# Test behavior when no more questions are available
def test_get_next_question_no_questions(mock_profile):
    mock_profile.remaining_questions = []
    with pytest.raises(Exception, match="No more questions to ask"):
        mock_profile.get_next_question()


# Test retrieving the next question from the remaining questions
def test_get_next_question(mock_profile):
    mock_profile.remaining_questions = [
        Question(
            id=1,
            body="What is your gender?",
            answers=[{"payload": 1, "title": "Female"}],
            change=Gender,
            put_payload="gender",
        )
    ]
    message, question_id = mock_profile.get_next_question()
    assert message["text"] == "What is your gender?"
    assert question_id == 1


# Test whether the system needs to ask about the user profile based on conversation statistics
def test_need_to_ask_about_profile(
    mock_profile, conversation, conversation_statistics, empty_tracker
):
    should_ask, next_count = mock_profile.need_to_ask_about_profile(
        conversation, conversation_statistics, empty_tracker
    )
    assert should_ask is False
    assert next_count == -1

from enum import IntEnum
import random
from .ej_api import EjApi
from .conversation import Conversation
from rasa_sdk.events import SlotSet
import json

PATH_PROFILE_QUESTIONS = "../profile-questions.json"


class Profile:
    def __init__(self, tracker):
        self.ej_api: EjApi = EjApi(tracker)
        self.questions: Question = []
        self.user_profile: UserProfile = self.get_user_profile()
        self.set_attributes()
        self.remaining_questions = self.set_remaining_questions()

    def get_user_profile(self):
        """
        get profile by ej-api
        """
        response = self.ej_api.request_profile()
        data = response.json()
        return UserProfile(data)

    def set_remaining_questions(self):
        """
        set remaining questions
        """
        if self.user_profile.age_range == AgeRange.NOT_FILLED:
            self.remaining_questions.append(
                q for q in self.questions if q.change == AgeRange
            )
        if self.user_profile.ethnicity_choices == Ethnicity.NOT_FILLED:
            self.remaining_questions.append(
                q for q in self.questions if q.change == Ethnicity
            )
        if self.user_profile.gender == Gender.NOT_FILLED:
            self.remaining_questions.append(
                q for q in self.questions if q.change == Gender
            )
        if self.user_profile.region == Region.NOT_FILLED:
            self.remaining_questions.append(
                q for q in self.questions if q.change == Region
            )

        self.remaining_questions.sort(key=lambda x: x.id)

    def set_attributes(self):
        with open(PATH_PROFILE_QUESTIONS) as f:
            data = json.load(f)
            self.user_profile
            self.questions = self.get_questions(data)
            self.random_questions = data["random_questions"]

    def get_questions(self, data):
        """
        get questions by profile-questions.json
        """
        questions: Question = []

        for question in data:
            id = question["id"]
            body = question["body"]
            answers = question["answers"]
            tmp_change = question["change"]

            if tmp_change == Ethnicity.name:
                change = Ethnicity
            elif tmp_change == Region.name:
                change = Region
            elif tmp_change == Gender.name:
                change = Gender
            elif tmp_change == AgeRange.name:
                change = AgeRange

            questions.append(Question(id, body, answers, change))
        return questions

    def get_next_question(self):
        """
        get next question
        """
        if len(self.remaining_questions) == 0:
            raise Exception("No more questions to ask")

        if self.random_questions:
            random_number = random.randint(0, len(self.remaining_questions) - 1)
            return self.remaining_questions.pop(random_number)

        # remaining_questions is sorted by id
        next_question = self.remaining_questions.pop(0)

        message = {"text": next_question.body, "buttons": next_question.answers}
        id = next_question.id

        return message, id

    def need_to_ask_about_profile(self, conversation_statistics, tracker):
        """
        check if need to ask about profile
        """
        if len(self.remaining_questions) == 0:
            return False

        if tracker.get_slot("sended_profile_question"):
            return False

        if Conversation.get_send_profile_questions(conversation_statistics):
            current_votes = Conversation.get_user_voted_comments_counter(
                conversation_statistics
            )
            votes_to_send_profile_questions = (
                Conversation.get_votes_to_send_profile_questions(
                    conversation_statistics
                )
            )
            if current_votes >= votes_to_send_profile_questions:
                return True
        return False

    def is_valid_answer(self, answer, id_question):
        """
        check if answer is valid
        """
        question = [self.questions for q in self.questions if q.id == id_question]

        if len(question) == 1:
            return answer in question[0].answers
        else:
            return False


class Question:
    def __init__(self, id, body, answers, change):
        self.id = id
        self.body = body
        self.answers = answers
        self.change = change


class UserProfile:
    def __init__(self, data):
        """
        data:

        "user": 0,
        "phone_number": "",
        "ethnicity_choices": 0,
        "race": 0,
        "gender": 0,
        "birth_date": null,
        "age_range": 0,
        "region": 0
        """
        self.user = data["user"]
        self.phone_number = data["phone_number"]
        self.ethnicity_choices = data["ethnicity_choices"]
        self.gender = data["gender"]
        self.age_range = data["age_range"]
        self.region = data["region"]


# Enums


class Ethnicity(IntEnum):
    NOT_FILLED = 0
    INDIGENOUS = 1
    BLACK = 2
    BROWN = 3
    WHITE = 4
    YELLOW = 5
    PREFER_NOT_TO_SAY = 6


class Region(IntEnum):
    NOT_FILLED = 0
    NORTH = 1
    NORTHEAST = 2
    MIDWEST = 3
    SOUTHEAST = 4
    SOUTH = 5


class Gender(IntEnum):
    NOT_FILLED = 0
    FEMALE = 1
    MALE = 2
    NO_BINARY = 3
    PREFER_NOT_TO_SAY = 20  # need add to ej api


class AgeRange(IntEnum):
    NOT_FILLED = 0
    RANGE_1 = 1
    RANGE_2 = 2
    RANGE_3 = 3
    RANGE_4 = 4
    RANGE_5 = 5
    RANGE_6 = 6

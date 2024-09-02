from enum import IntEnum
import json
import os
import random

from actions.logger import custom_logger

from .settings import PROFILE, PUT_PROFILE
from .conversation import Conversation
from .ej_api import EjApi


class Profile:
    def __init__(self, tracker):
        self.ej_api: EjApi = EjApi(tracker)
        self.questions: Question = []
        self.get_profile()
        self.set_attributes()
        self.remaining_questions: Question = self.set_remaining_questions()

    def get_profile(self):
        """
        get profile by ej-api
        """
        response = self.ej_api.request(PROFILE)
        data = response.json()
        self.user = data["user"]
        self.phone_number = data["phone_number"]
        self.ethnicity_choices = data["ethnicity_choices"]
        self.gender = data["gender"]
        self.age_range = data["age_range"]
        self.region = data["region"]

    def set_remaining_questions(self):
        """
        set remaining questions
        """
        remaining_questions = []
        if self.age_range == AgeRange.NOT_FILLED:
            remaining_questions.extend(
                [q for q in self.questions if q.change == AgeRange]
            )
        if self.ethnicity_choices == Ethnicity.NOT_FILLED:
            remaining_questions.extend(
                [q for q in self.questions if q.change == Ethnicity]
            )
        if self.gender == Gender.NOT_FILLED:
            remaining_questions.extend(
                [q for q in self.questions if q.change == Gender]
            )
        if self.region == Region.NOT_FILLED:
            remaining_questions.extend(
                [q for q in self.questions if q.change == Region]
            )

        # sort by id
        remaining_questions.sort(key=lambda x: x.id)
        return remaining_questions

    def set_attributes(self):
        questions_file = (
            f"{str(os.path.dirname(os.path.realpath(__file__)))}/profile-questions.json"
        )
        with open(questions_file) as f:
            data = json.load(f)
            self.questions = self.get_questions(data)
            self.random_questions = data["random_questions"]

    def get_questions(self, data):
        """
        get questions by profile-questions.json
        """
        questions: Question = []

        for question in data["questions"]:
            id = int(question["id"])
            body = question["body"]
            answers = question["answers"]
            tmp_change = question["change"]
            put_payload = question["put_payload"]

            if tmp_change == "Ethnicity":
                change = Ethnicity
            elif tmp_change == "Region":
                change = Region
            elif tmp_change == "Gender":
                change = Gender
            elif tmp_change == "AgeRange":
                change = AgeRange

            questions.append(Question(id, body, answers, change, put_payload))
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

    def need_to_ask_about_profile(
        self, conversation: Conversation, conversation_statistics, tracker
    ):
        """
        check if need to ask about profile
        """
        custom_logger("need_to_ask_about_profile")
        if len(self.remaining_questions) == 0:
            custom_logger("NO MORE QUESTIONS")
            return False, -1

        if not conversation.send_profile_question:
            custom_logger("conversation.send_profile_question: False")
            return False, -1

        if conversation.send_profile_question:
            current_votes = Conversation.get_user_voted_comments_counter(
                conversation_statistics
            )
            votes_to_send_profile_questions = (
                conversation.votes_to_send_profile_questions
            )
            next_value_to_send_profile_questions = tracker.get_slot(
                "next_count_to_send_profile_question"
            )

            if not next_value_to_send_profile_questions:
                next_value_to_send_profile_questions = current_votes
            else:
                next_value_to_send_profile_questions = int(
                    next_value_to_send_profile_questions
                )

            if (
                current_votes >= votes_to_send_profile_questions
                and next_value_to_send_profile_questions == current_votes
            ):
                custom_logger("need_to_ask_about_profile: True")
                next_value_to_send_profile_questions += 2
                return True, next_value_to_send_profile_questions
        custom_logger("need_to_ask_about_profile: False")
        return False, -1

    def is_valid_answer(self, answer, id_question):
        """
        check if answer is valid
        """
        question: Question = None
        for q in self.questions:
            if q.id == id_question:
                question = q
                break
        err = None
        if question:
            try:
                answer = int(answer)
            except ValueError as err:
                custom_logger(f"Answer {answer} is not a valid integer")
                return False, err

            for a in question.answers:
                if a["payload"] == answer:
                    response = self.send_answer(answer, question)
                    if response.status_code == 200:
                        return True, err
                    else:
                        err = response.status_code
                        return False, err
        return False, err

    def send_answer(self, answer, question):
        """
        send answer to ej-api
        """
        data = {question.put_payload: answer}
        custom_logger(f"Sending answer {data} to ej-api")
        json_data = json.dumps(data)
        response = self.ej_api.request(self.put_url(), json_data, put=True)
        custom_logger(f"Response: {response.json()}")
        return response

    def put_url(self):
        return f"{PUT_PROFILE}{self.user}/"

    @staticmethod
    def finish_profile(slot_value: str):
        """
        Rasa ends a form when all slots are filled. This method
        fills the profile_form slots with slot_value,
        forcing Rasa to stop sending comments to voting.
        """
        return {"profile_question": slot_value, "need_to_ask_profile_question": False}

    @staticmethod
    def continue_profile():
        """
        Rasa continues the profile form.
        """
        return {"profile_question": None}


class Question:
    def __init__(self, id, body, answers, change, put_payload):
        self.id = id
        self.body = body
        self.answers = answers
        self.change = change
        self.put_payload = put_payload


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

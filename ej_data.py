from enum import IntEnum

CSV_COLUMNS = {
    "user": 1,
    "ethnicity_choices": 0,
    "gender": 0,
    "age_range": 0,
    "region": 0,
}


class Ethnicity(IntEnum):
    """
    indígena
    preta
    parda
    branca
    amarela
    prefiro não dizer
    """

    NOT_FILLED = 0
    INDIGENOUS = 1
    BLACK = 2
    BROWN = 3
    WHITE = 4
    YELLOW = 5
    PREFER_NOT_TO_SAY = 6


class Region(IntEnum):
    """
    1) Norte
    2) Nordeste
    3) Centro-Oeste
    4) Sudeste
    5) Sul
    """

    NOT_FILLED = 0
    NORTH = 1
    NORTHEAST = 2
    MIDWEST = 3
    SOUTHEAST = 4
    SOUTH = 5


class Gender(IntEnum):
    """
    1) Feminino
    2) Masculino
    3) Não-binário [se identifica fora do binário de gênero]
    4) Prefiro não dizer
    """

    NOT_FILLED = 0
    FEMALE = 1
    MALE = 2
    NO_BINARY = 3
    PREFER_NOT_TO_SAY = 20  # need add to ej api


class AgeRange(IntEnum):
    """
    1) Menos de 17 anos
    2) Entre 17-20 anos
    3) Entre 21-29 anos
    4) Entre 30-45 anos
    5) Entre 45-60 anos
    6) Acima de 60 anos
    """

    NOT_FILLED = 0
    RANGE_1 = 1
    RANGE_2 = 2
    RANGE_3 = 3
    RANGE_4 = 4
    RANGE_5 = 5
    RANGE_6 = 6

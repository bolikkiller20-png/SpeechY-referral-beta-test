from enum import Enum


class DifficultyLevel(str, Enum):
    EASY = 'easy'
    MEDIUM = 'medium'
    HARD = 'hard'


class CourseName(str, Enum):
    IMPROVISATION = "Импровизация"
    DICTION = "Дикция"


class StreakStatus(str, Enum):
    INCREASED = "increased"
    RESET = "reset"
    FIRST_TASK = "first_task"
    ALREADY_COMPLETED = "already_completed"
    STREAK_BROKEN = "streak_broken"


class ImprovizationTaskName(str, Enum):
    DESCRIPTION_OF_THE_ITEM = "Описание предмета"
    RETELL = "Пересказ"
    NEW_WORD = "Новое слово"


class DictionTaskName(str, Enum):
    TONGUE_TWISTER = "Скороговорка"
    VOWELS_AND_CONSONANTS = "Гласные/согласные"


class PromoCodeTypes(str, Enum):
    DISCOUNT = "discount"
    TRIALS = "trials"


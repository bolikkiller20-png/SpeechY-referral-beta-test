from abc import ABC, abstractmethod

from database.models import Task, Condition
from schemas.schemas import CourseName, ImprovizationTaskName, DictionTaskName


class MessageFormatter(ABC):

    """
    Abstract base class for message formatting
    """

    @abstractmethod
    def format_task_message(
            self,
            task: Task,
            condition: Condition
    ) -> str:
        pass


class ImprovizationFormatter(MessageFormatter):
    """
    Formatter for improvization course
    """

    def format_task_message(
            self,
            task: Task,
            condition: Condition
    ) -> str:
        if task.name == ImprovizationTaskName.DESCRIPTION_OF_THE_ITEM:
            return (
                f"🎭 Задание: <b><i>{task.name}</i></b>\n\n"
                f"📋 <i>{task.rules}</i>\n\n"
                f"🎲 Твое слово: <b>{condition.condition}</b>\n\n"
                f"💡 Говори без остановки 60 секунд!"
            )
        elif task.name == ImprovizationTaskName.RETELL:
            return (
                f"🎭 Задание: <b><i>{task.name}</i></b>\n\n"
                f"📋 <i>{task.rules}</i>\n\n"
                f"🎲 Твой текст: <b>{condition.condition}</b>\n\n"
                f"💡 Ты должен пересказать текст минимум за 1 минуту\n"
                f"Как будешь готов нажми на кнопку ниже"
            )
        elif task.name == ImprovizationTaskName.NEW_WORD:
            return (
                f"🎭 Задание: <b><i>{task.name}</i></b>\n\n"
                f"📋 <i>{task.rules}</i>\n\n"
                f"🎲 <b>{condition.condition}</b>\n\n"
                f"Записывай голосовое длиной минимум в 1 минуту"
            )


class DictionFormatter(MessageFormatter):
    def format_task_message(
            self,
            task: Task,
            condition: Condition
    ) -> str:
        if task.name == DictionTaskName.TONGUE_TWISTER:
            return (
                f"🎭 Задание: <b><i>{task.name}</i></b>\n\n"
                f"📋 <i>{task.rules}</i>\n\n"
                f"🎲 <b>{condition.condition}</b>\n\n"
            )
        elif task.name == DictionTaskName.VOWELS_AND_CONSONANTS:
            print("Зашли в согласные/гласныеч")
            return (
                f"🎭 Задание: <b><i>{task.name}</i></b>\n\n"
                f"📋 <i>{task.rules}</i>\n\n"
                f"🎲 <b>{condition.condition}</b>\n\n"
            )


class MessageFormatterFactory:
    """
    Factory for creating formatters based on course name
    """

    _formatters = {
        CourseName.IMPROVISATION: ImprovizationFormatter(),
        CourseName.DICTION: DictionFormatter()
    }

    @classmethod
    def get_formatter(cls, course_name: CourseName) -> MessageFormatter:
        """
        Get formatter for specific course
        :param course_name:
        :return: formatter
        """

        formatter = cls._formatters.get(course_name)
        if not formatter:
            raise ValueError(
                f"No formatter found for course {course_name}"
            )
        return formatter


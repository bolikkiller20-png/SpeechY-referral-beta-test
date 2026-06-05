from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import exists

from constants.Constants import Constants
from database.models import Course, Task, Condition, PromoCode
from database.repositories.ConditionRepository import ConditionRepository
from database.repositories.CourseRepository import CourseRepository
from database.repositories.PromoCodeRepository import PromoCodeRepository
from database.repositories.TaskRepository import TaskRepository
from schemas.schemas import CourseName


class DataSeeder:
    constants = Constants()
    available_courses = constants.get_const_courses()
    improvisation_tasks = constants.get_const_improvisation_tasks()
    diction_tasks = constants.get_const_diction_tasks()

    # Добавляем промокоды как атрибут класса
    PROMO_CODES = constants.get_promo_codes()

    def __init__(self, session: AsyncSession):
        self.session = session
        self.course_repo = CourseRepository(session)
        self.task_repo = TaskRepository(session)
        self.condition_repo = ConditionRepository(session)
        self.promo_code_repo = PromoCodeRepository(session)

    async def update_seed_data(self, course_names: list[str] = None) -> None:
        """
        Обновляет существующие данные, не удаляя их
        """
        print(f"=== НАЧАЛО ОБНОВЛЕНИЯ ДАННЫХ ===")

        # 1. Обновляем курсы и задания
        await self._update_courses_and_tasks(course_names)

        # 2. Обновляем промокоды
        await self._update_promo_codes()
        deactivated = await self.promo_code_repo.deactivate_expired_promo_codes()
        if deactivated > 0:
            print(f"  ⏰ Деактивировано {deactivated} просроченных промокодов")
        await self.session.commit()
        print(f"=== ОБНОВЛЕНИЕ ЗАВЕРШЕНО ===")

    async def _update_courses_and_tasks(self, course_names: list[str] = None) -> None:
        """
        Обновляет курсы и задания
        """
        courses_to_process = course_names or [course["name"] for course in self.available_courses]

        # Обновляем курсы
        for course_data in self.available_courses:
            if course_data["name"] not in courses_to_process:
                continue

            result = await self.session.execute(
                select(Course).where(Course.name == course_data["name"])
            )
            course = result.scalar_one_or_none()

            if course:
                course.description = course_data.get("description", course.description)
                course.is_active = course_data.get("is_active", course.is_active)
            else:
                self.session.add(Course(**course_data))

        await self.session.flush()

        # Обрабатываем задания для каждого запрошенного курса
        for course_name in courses_to_process:
            result = await self.session.execute(
                select(Course.id).where(Course.name == course_name)
            )
            course_id = result.scalar_one_or_none()

            if not course_id:
                raise ValueError(f"Курс {course_name} не найден")

            tasks_data = self._get_tasks_for_course(course_name)

            for task_data in tasks_data:
                result = await self.session.execute(
                    select(Task).where(
                        Task.name == task_data["name"],
                        Task.course_id == course_id
                    )
                )
                task = result.scalar_one_or_none()

                if task:
                    task.rules = task_data.get("rules", task.rules)
                else:
                    task = Task(
                        course_id=course_id,
                        name=task_data["name"],
                        rules=task_data["rules"]
                    )
                    self.session.add(task)
                    await self.session.flush()

                # Обновляем условия
                for condition_group in task_data.get("conditions", []):
                    difficulty = condition_group["difficulty_level"]
                    for condition_text in condition_group["conditions"]:
                        result = await self.session.execute(
                            select(Condition).where(
                                Condition.task_id == task.id,
                                Condition.condition == condition_text,
                                Condition.difficulty_level == difficulty
                            )
                        )
                        existing = result.scalar_one_or_none()

                        if not existing:
                            self.session.add(
                                Condition(
                                    task_id=task.id,
                                    condition=condition_text,
                                    difficulty_level=difficulty
                                )
                            )

    async def _update_promo_codes(self) -> None:
        """
        Обновляет или добавляет промокоды из списка PROMO_CODES
        """
        print("Обновление промокодов...")

        for promo_data in self.PROMO_CODES:
            # Проверяем, существует ли уже такой промокод
            result = await self.session.execute(
                select(PromoCode).where(PromoCode.code == promo_data["code"])
            )
            existing_promo = result.scalar_one_or_none()

            if existing_promo:
                # Обновляем существующий
                existing_promo.reward_type = promo_data.get("reward_type", existing_promo.reward_type)
                existing_promo.reward_value = promo_data.get("reward_value", existing_promo.reward_value)
                existing_promo.max_uses = promo_data.get("max_uses", existing_promo.max_uses)
                existing_promo.user_limit = promo_data.get("user_limit", existing_promo.user_limit)
                existing_promo.is_active = promo_data.get("is_active", existing_promo.is_active)
                existing_promo.expires_at = promo_data.get("expires_at", existing_promo.expires_at)
                print(f"  ✅ Обновлён промокод: {promo_data['code']}")
            else:
                # Создаём новый
                new_promo = PromoCode(
                    code=promo_data["code"],  # предполагая, что поле называется 'name'
                    reward_type=promo_data["reward_type"],
                    reward_value=promo_data["reward_value"],
                    max_uses=promo_data["max_uses"],
                    user_limit=promo_data.get("user_limit", 1),
                    is_active=promo_data.get("is_active", True),
                    expires_at=promo_data.get("expires_at"),
                    used_count=0  # начальное значение
                )
                self.session.add(new_promo)
                print(f"  ✅ Добавлен новый промокод: {promo_data['code']}")

        await self.session.flush()
        print(f"Обновление промокодов завершено. Всего промокодов: {len(self.PROMO_CODES)}")

    def _get_tasks_for_course(self, course_name: str) -> list:
        """
        Возвращает задания для конкретного курса
        """
        if course_name == CourseName.IMPROVISATION.value:
            return self.improvisation_tasks
        elif course_name == CourseName.DICTION.value:
            return self.diction_tasks
        else:
            return []

    async def seed_all(self) -> None:
        """
        Первоначальное заполнение всех данных (очищает существующие)
        """
        for course in self.available_courses:
            print("Добавление курса", course)
            await self.course_repo.create(**course)

        for improvisation_task in self.improvisation_tasks:
            await self.task_repo.add_task("Импровизация", improvisation_task["name"], improvisation_task["rules"])
            for conditions_group in improvisation_task["conditions"]:
                for condition_text in conditions_group["conditions"]:
                    await self.condition_repo.add_condition(
                        improvisation_task["name"],
                        condition_text,
                        conditions_group["difficulty_level"]
                    )

        await self._update_promo_codes()
        await self.session.commit()
from typing import List, Optional, Union, Annotated

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories.AnchorRepository import AnchorRepository
from database.repositories.UserRepository import UserRepository
from logger_config import app_logger


class AnchorMessageManager:
    def __init__(
            self,
            user_id: int,
            chat_id: int,
            bot: Bot,
            session: AsyncSession,
            state: FSMContext
    ):
        self.user_id = user_id
        self.chat_id = chat_id
        self.bot = bot
        self.session = session
        self.state = state
        self.anchor_repo = AnchorRepository(session)

        self._temp_messages: List[int] =[]
        self.notification_message_ids: List[int] = []

    async def get_anchor_id(self) -> Optional[int]:
        anchor = await self.anchor_repo.get_anchor(self.user_id)
        return anchor.anchor_message_id if anchor else None

    async def save_anchor(self, message_id: int):
        await self.anchor_repo.save_anchor(
            user_id=self.user_id,
            chat_id=self.chat_id,
            message_id=message_id
        )

    async def send_anchor(
            self,
            text: str,
            reply_markup: Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, None] = None
    ) -> Message:
        old_anchor_id = await self.get_anchor_id()
        if old_anchor_id:
            try:
                await self.bot.delete_message(self.chat_id, old_anchor_id)
            except (TelegramBadRequest, TelegramForbiddenError) as e:
                app_logger.debug(f"Не удалось удалить старый якорь: {e}")

        msg = await self.bot.send_message(
            chat_id=self.chat_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        await self.save_anchor(msg.message_id)
        return msg

    async def edit_anchor(
            self,
            text: str,
            reply_markup: Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, None] = None,
            parse_mode: Optional[ParseMode] = ParseMode.HTML
    ) -> Optional[Message]:
        anchor_id = await self.get_anchor_id()
        print(f"📌 edit_anchor вызван: anchor_id={anchor_id}, chat_id={self.chat_id}")
        if anchor_id:
            try:
                msg = await self.bot.edit_message_text(
                    text=text,
                    chat_id=self.chat_id,
                    message_id=anchor_id,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
                return msg

            except TelegramBadRequest as e:
                error_msg = str(e).lower()

                if "message to edit not found" in error_msg:
                    app_logger.info(f"Якорь {anchor_id} не найден, создаю новый")

                elif "message is not modified" in error_msg:
                    app_logger.debug(f"Сообщение не изменилось, пропускаем")
                    return None

                else:
                    app_logger.error(f"Ошибка редактирования якоря: {e}")

            except Exception as e:
                app_logger.error(f"Неожиданная ошибка при редактировании: {e}")

        return await self.send_anchor(text, reply_markup)

    async def update_anchor_text(
            self,
            text: str,
    ):
        return await self.edit_anchor(text, reply_markup=None)

    async def delete_anchor(self) -> bool:
        anchor_id = await self.get_anchor_id()
        if anchor_id:
            try:
                await self.bot.delete_message(self.chat_id, anchor_id)
            except Exception as e:
                app_logger.debug(f"Не удалось удалить якорь: {e}")

        return await self.anchor_repo.delete_anchor(self.user_id)

    async def delete_user_message(self, message: Message) -> bool:
        try:
            await message.delete()
            return True
        except Exception as e:
            app_logger.debug(f"Не удалось удалить сообщение пользователя: {e}")
            return False

    @staticmethod
    async def get_anchor_manager(
            event: Annotated[Message | CallbackQuery, ...],
            session: AsyncSession,
            user_repo: UserRepository,
            state: FSMContext
    ):
        user = await user_repo.get_by_telegram_id(event.from_user.id)

        if isinstance(event, Message):
            chat_id = event.chat.id
        elif isinstance(event, CallbackQuery):
            chat_id = event.message.chat.id
        else:
            raise ValueError("Cannot determine chat_id")
        return AnchorMessageManager(
            user_id=user.id,
            chat_id=chat_id,
            bot=event.bot,
            session=session,
            state=state
        )

    async def _get_notification_key(self) -> str:
        return f"notification_messages_{self.user_id}_{self.chat_id}"

    async def _get_temp_key(self) -> str:
        """
        :return:
        Ключ для хранения temp сообщений в FSM
        """
        return f"temp_messages_{self.user_id}_{self.chat_id}"

    async def get_notification_messages(self) -> List[int]:
        if self.state:
            data = await self.state.get_data()
            return data.get('notification_messages', [])
        return []

    async def get_temp_messages(self) -> List[int]:
        """
        :return:
        Получить temp сообщения из FSM
        """
        if self.state:
            data = await self.state.get_data()
            return data.get('temp_messages', [])
        return self._temp_messages

    async def save_notification_messages(self, messages: List[int]):
        if self.state:
            await self.state.update_data(notification_messages=messages)

    async def save_temp_messages(self, messages: List[int]):
        if self.state:
            await self.state.update_data(temp_messages=messages)
        else:
            self._temp_messages = messages

    async def add_notification_message(self, message_id: int):
        messages = await self.get_notification_messages()
        messages.append(message_id)
        await self.save_notification_messages(messages)
        app_logger.debug(f"Добавлено уведомление {message_id}, всего: {len(messages)}")

    async def add_temp_message(self, message: Message):
        if message and message.message_id:
            temp_messages = await self.get_temp_messages()
            temp_messages.append(message.message_id)
            await self.save_temp_messages(temp_messages)
            app_logger.debug(f"Добавлено temp сообщение {message.message_id}, всего: {len(temp_messages)}")
            print(f"Temp после добавления: {temp_messages}")

    async def delete_all_notification_messages(self, bot: Bot, chat_id: int) -> int:
        messages = await self.get_notification_messages()
        if not messages:
            return 0
        deleted_count = 0
        for msg_id in messages:
            try:
                await bot.delete_message(chat_id, msg_id)
                deleted_count += 1
            except Exception as e:
                app_logger.debug(f"Не удалось удалить {msg_id}: {e}")
        await self.save_notification_messages([])
        app_logger.debug(f"Удалено {deleted_count} сообщений")
        return deleted_count

    async def add_temp_messages(self, messages: List[Message]) -> None:
        for msg in messages:
            await self.add_temp_message(msg)

    async def delete_all_temp_messages(self) -> int:
        """
        :return:
        Количество удаленных сообщений
        """
        temp_messages = await self.get_temp_messages()
        if not temp_messages:
            app_logger.debug("Нет временных сообщений для удаления")
            return 0

        deleted_count = 0
        messages_for_delete = temp_messages.copy()

        for message_id in messages_for_delete:
            try:
                await self.bot.delete_message(
                    self.chat_id,
                    message_id
                )
                deleted_count += 1
                app_logger.debug(f"Удалено сообщение {message_id}")
            except TelegramBadRequest as e:
                if "message to delete not found" in str(e).lower():
                    app_logger.debug(f"Сообщение {message_id} уже удалено")
                    deleted_count += 1
                else:
                    app_logger.debug(f"Не удалось удалить сообщение {message_id}: {e}")
            except Exception as e:
                app_logger.debug(f"Ошибка при удалении сообщения {message_id}: {e}")

            await self.save_temp_messages([])

            app_logger.debug(f"Удалено {deleted_count} из {len(messages_for_delete)} временных сообщений")
            print(f"Удалено {deleted_count} сообщений")
            return deleted_count

    async def clear_temp_messages(self) -> None:
        await self.save_temp_messages([])

    async def get_temp_messages_count(self) -> int:
        return len(await self.get_temp_messages())







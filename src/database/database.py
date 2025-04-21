from __future__ import annotations

import asyncio
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Column, Integer, String, DateTime


class Base(AsyncAttrs, DeclarativeBase):
    pass


class GroupChats(Base):
    __tablename__ = 'groupchats'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    status: Mapped[str] = mapped_column(String, default='test')
    channel_id: Mapped[int] = mapped_column(Integer, default=0)


class Database:
    def __init__(self, db_url: str = "sqlite+aiosqlite:///src/database/telegram_clients.db"):
        self.engine = create_async_engine(db_url, echo=True)
        self.async_session = async_sessionmaker(
            self.engine, expire_on_commit=False
        )

    async def create_tables(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def close(self):
        await self.engine.dispose()

    # GroupChats CRUD operations
    async def create_group_chat(
            self,
            name: str,
            status: str = 'test',
            channel_id: int = 0
    ) -> GroupChats:
        async with self.async_session() as session:
            group_chat = GroupChats(
                name=name,
                status=status,
                channel_id=channel_id
            )
            session.add(group_chat)
            await session.commit()
            await session.refresh(group_chat)
            return group_chat

    async def get_group_chat(self, chat_id: int) -> Optional[GroupChats]:
        async with self.async_session() as session:
            result = await session.execute(
                select(GroupChats).where(GroupChats.id == chat_id))
            return result.scalar_one_or_none()

    async def get_group_chat_by_name(self, name: str) -> Optional[GroupChats]:
        async with self.async_session() as session:
            result = await session.execute(
                select(GroupChats).where(GroupChats.name == name))
            return result.scalar_one_or_none()

    async def get_all_group_chats(self) -> List[GroupChats]:
        async with self.async_session() as session:
            result = await session.execute(select(GroupChats))
            return list(result.scalars())

    async def get_chats_by_status(self, status: str) -> List[GroupChats]:
        """
        Получить все групповые чаты с указанным статусом

        :param status: Значение статуса для фильтрации
        :return: Список объектов GroupChats
        """
        async with self.async_session() as session:
            result = await session.execute(
                select(GroupChats)
                .where(GroupChats.status == status)
                .order_by(GroupChats.created_at)
            )
            return list(result.scalars().all())

    async def update_group_chat(
            self,
            chat_id: int,
            name: Optional[str] = None,
            status: Optional[str] = None,
            channel_id: Optional[int] = None
    ) -> Optional[GroupChats]:
        async with self.async_session() as session:
            stmt = update(GroupChats).where(GroupChats.id == chat_id)
            if name is not None:
                stmt = stmt.values(name=name)
            if status is not None:
                stmt = stmt.values(status=status)
            if channel_id is not None:
                stmt = stmt.values(channel_id=channel_id)

            await session.execute(stmt)
            await session.commit()

            return await self.get_group_chat(chat_id)

    async def delete_group_chat(self, chat_id: int) -> bool:
        async with self.async_session() as session:
            result = await session.execute(
                delete(GroupChats).where(GroupChats.id == chat_id)
            )
            await session.commit()
            return result.rowcount > 0


# Пример использования
async def main():
    db = Database("sqlite+aiosqlite:///telegram_clients.db")
    chats = await db.get_chats_by_status(status='test')
    # await db.create_tables()
    #
    # # Создание чата
    # chat = await db.create_group_chat(name="Test Chat")
    # print(f"Created chat: {chat.name}, ID: {chat.id}")
    #
    # # Получение чата
    # fetched_chat = await db.get_group_chat(chat.id)
    # print(f"Fetched chat: {fetched_chat.name}")
    #
    # # Обновление чата
    # updated_chat = await db.update_group_chat(chat.id, status="active")
    # print(f"Updated status: {updated_chat.status}")
    #
    # # Удаление чата
    # deleted = await db.delete_group_chat(chat.id)
    # print(f"Chat deleted: {deleted}")


    for chat in chats:
        print(f"Название : {chat.name}, Status : {chat.status}")
        #updated_chat = await db.update_group_chat(chat.id, status="test")
        #print(f"Updated Название : {updated_chat.name}, status: {updated_chat.status}")
    await db.close()

if __name__ == "__main__":
    asyncio.run(main())

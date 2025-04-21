# models.py
from enum import Enum
import uuid
from datetime import datetime
from typing import Any, Optional, Coroutine, Dict
import asyncio


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"  # Обратите внимание на двойное L (британский вариант)

    def is_terminal(self) -> bool:
        """Проверяет, является ли статус конечным (задача завершена)"""
        return self in {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED}


class Task:
    def __init__(self, coro: Coroutine, name: Optional[str] = None):
        self.id: str = str(uuid.uuid4())
        self.name: str = name or f"Task-{self.id[:8]}"
        self.coro: Coroutine = coro
        self._status: TaskStatus = TaskStatus.PENDING
        self._result: Optional[Any] = None
        self._error: Optional[Exception] = None
        self._task: Optional[asyncio.Task] = None
        self._created_at: Optional[datetime] = None
        self._started_at: Optional[datetime] = None
        self._completed_at: Optional[datetime] = None

    @property
    def status(self) -> TaskStatus:
        return self._status

    def set_status(self, status: TaskStatus) -> None:
        self._status = status

    @property
    def result(self) -> Optional[Any]:
        return self._result

    def set_result(self, result: Any) -> None:
        self._result = result

    @property
    def error(self) -> Optional[Exception]:
        return self._error

    def set_error(self, error: Exception) -> None:
        self._error = error

    @property
    def task(self) -> Optional[asyncio.Task]:
        return self._task

    def set_task(self, task: asyncio.Task) -> None:
        self._task = task

    @property
    def is_running(self) -> bool:
        return self._task is not None and not self._task.done()

    @property
    def created_at(self) -> Optional[datetime]:
        return self._created_at

    def set_created_at(self, created_at: datetime) -> None:
        self._created_at = created_at

    @property
    def started_at(self) -> Optional[datetime]:
        return self._started_at

    def set_started_at(self, started_at: datetime) -> None:
        self._started_at = started_at

    @property
    def completed_at(self) -> Optional[datetime]:
        return self._completed_at

    def set_completed_at(self, completed_at: datetime) -> None:
        self._completed_at = completed_at

    def __repr__(self) -> str:
        return f"Task(id={self.id}, name={self.name}, status={self.status.value})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": str(self.error) if self.error else None
        }
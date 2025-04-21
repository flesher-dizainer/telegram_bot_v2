# scheduler.py
import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional, List, Coroutine, Any, Set
from .models import Task, TaskStatus
from .exceptions import TaskNotFoundError, SchedulerNotRunningError


class TaskScheduler:
    """Асинхронный планировщик задач с явной инициализацией."""

    def __init__(self):
        self._tasks: Dict[str, Task] = {}
        self._running_tasks: Set[asyncio.Task] = set()
        self._lock = asyncio.Lock()
        self._is_running = False

    async def start(self) -> None:
        """Явно запускает планировщик перед использованием."""
        if self._is_running:
            raise RuntimeError("Scheduler already running")
        self._is_running = True
        logging.info("Планировщик задач запущен.")

    async def add_task(self, coro: Coroutine, name: Optional[str] = None) -> Task:
        """Добавляет новую задачу в планировщик."""
        if not self._is_running:
            raise SchedulerNotRunningError("Scheduler is not running. Call start() first.")

        async with self._lock:
            task = Task(coro, name)
            task.set_created_at(datetime.now())
            self._tasks[task.id] = task
            return task

    async def run_task(self, task: Task) -> None:
        """Запускает конкретную задачу."""
        if not self._is_running:
            raise SchedulerNotRunningError("Scheduler is not running")

        async with self._lock:
            if task.id not in self._tasks:
                raise TaskNotFoundError(task.id)

            if task.status != TaskStatus.PENDING:
                raise ValueError(f"Task {task.id} is already running or completed")

            await self._start_task(task)

    async def run_all_pending(self) -> None:
        """Запускает все ожидающие задачи."""
        if not self._is_running:
            raise SchedulerNotRunningError("Scheduler is not running")

        async with self._lock:
            pending_tasks = [t for t in self._tasks.values()
                             if t.status == TaskStatus.PENDING]
            for task in pending_tasks:
                await self._start_task(task)

    async def _start_task(self, task: Task) -> None:
        """Внутренний метод для запуска задачи."""
        task.set_status(TaskStatus.RUNNING)
        task.set_started_at(datetime.now())

        async def _wrapped_coro():
            try:
                result = await task.coro
                task.set_result(result)
                task.set_status(TaskStatus.COMPLETED)
            except asyncio.CancelledError:
                task.set_status(TaskStatus.CANCELLED)
                raise
            except Exception as e:
                task.set_error(e)
                task.set_status(TaskStatus.FAILED)
            finally:
                task.set_completed_at(datetime.now())
                async with self._lock:
                    self._running_tasks.discard(asyncio.current_task())

        asyncio_task = asyncio.create_task(_wrapped_coro())
        task.set_task(asyncio_task)
        self._running_tasks.add(asyncio_task)
        asyncio_task.add_done_callback(lambda t: self._running_tasks.discard(t))

    async def shutdown(self) -> None:
        """Корректно завершает работу планировщика."""
        async with self._lock:
            if not self._is_running:
                logging.info("Планировщик уже выключен.")
                return

            self._is_running = False
            tasks_to_cancel = list(self._running_tasks)
            for task in tasks_to_cancel:
                task.cancel()
            await asyncio.gather(*tasks_to_cancel, return_exceptions=True)
            logging.info("Планировщик выключен.")

    def get_task(self, task_id: str) -> Task:
        """Возвращает задачу по ID."""
        if task_id not in self._tasks:
            raise TaskNotFoundError(task_id)
        return self._tasks[task_id]

    def get_all_tasks(self) -> List[Task]:
        """Возвращает все задачи."""
        return list(self._tasks.values())

    def get_active_tasks(self) -> List[Task]:
        """Возвращает активные (выполняющиеся) задачи."""
        return [t for t in self._tasks.values()
                if t.status in {TaskStatus.PENDING, TaskStatus.RUNNING}]

    async def cancel_task(self, task_id: str) -> bool:
        """Отменяет задачу по ID."""
        async with self._lock:
            try:
                task = self.get_task(task_id)
            except TaskNotFoundError:
                return False

            if task.status.is_terminal():
                return False

            if task.task:
                task.task.cancel()
                try:
                    await task.task
                except (asyncio.CancelledError, Exception):
                    pass
                return True

            # Если задача еще не запущена (PENDING)
            task.set_status(TaskStatus.CANCELLED)
            task.set_completed_at(datetime.now())
            return True

    async def wait_for_task(self, task_id: str, timeout: Optional[float] = None) -> Task:
        """Ожидает завершения задачи с таймаутом."""
        task = self.get_task(task_id)

        if not task.task or task.status.is_terminal():
            return task

        try:
            await asyncio.wait_for(asyncio.shield(task.task), timeout)
        except (asyncio.TimeoutError, Exception):
            pass

        return task

    def task_status(self, task_id: str) -> TaskStatus:
        """Возвращает статус задачи."""
        return self.get_task(task_id).status

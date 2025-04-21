# exceptions.py
class TaskSchedulerError(Exception):
    """Базовое исключение для планировщика задач"""
    pass


class TaskNotFoundError(TaskSchedulerError):
    """Исключение, возникающее когда задача не найдена"""

    def __init__(self, task_id):
        self.task_id = task_id
        super().__init__(f"Task with ID {task_id} not found")


class SchedulerNotRunningError(Exception):
    """Исключение, возникающее при попытке выполнить операцию с планировщиком, который не был запущен."""

    def __init__(self, message: str = "Task scheduler is not running"):
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message

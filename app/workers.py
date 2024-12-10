import abc
from multiprocessing import Lock
from multiprocessing.pool import ThreadPool

from bus import AbstractBus
import time
from models import Command, WorkerCommandBody, CommandInfo


# Абстрактный класс, описывающий базовую логику для работников (воркеров).
class AbstractWorker(abc.ABC):

    @abc.abstractmethod
    def on_job(self, item):
        """
        Метод обработки задания.
        Каждый конкретный воркер должен реализовать эту логику.
        :param item: Задание, которое необходимо выполнить.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def start(self):
        """
        Метод старта работы воркера. Ожидает и выполняет задания.
        """
        raise NotImplementedError


# Базовая реализация воркера, использующая шину данных для обмена сообщениями.
class BaseWorker(AbstractWorker):

    def __init__(self, name: str, bus: AbstractBus):
        """
        Инициализация базового воркера.

        :param name: Имя воркера.
        :param bus: Шина для обмена сообщениями с другими компонентами.
        """
        self.bus = bus  # Шина для отправки и получения сообщений
        self.name = name  # Имя воркера
        self.lock = Lock()  # Блокировка для синхронизации доступа к ресурсу
        self.task = self._count = 0  # Счётчик задач и текущего задания

        self.start()  # Запуск воркера

    def start(self):
        """
        Основной цикл работы воркера. Воркер будет постоянно проверять шину
        на наличие новых команд.
        В зависимости от типа команды, воркер выполнит нужное действие.
        """
        while True:
            if self.bus.pool(
                timeout=2.0
            ):  # Проверка доступности команды в шине
                command = self.bus.get()  # Получение команды
                match command["name"]:
                    case "add":
                        # Если команда "add",
                        # то асинхронно вызываем метод on_job
                        ThreadPool().apply_async(
                            self.on_job, args=(command["body"],)
                        )
                    case "info":
                        # Если команда "info", отправляем информацию
                        # о текущем состоянии воркера
                        self.bus.put(
                            CommandInfo(
                                name="info",
                                body=WorkerCommandBody(
                                    name=self.name, number=self._count
                                ),
                            )
                        )

    def on_job(self, item: int):
        """
        Метод для выполнения задания.
        Воркеры выполняют задачу, обновляя свой счётчик.

        :param item: Количество единиц работы (например, секунд или шагов).
        """
        with (
            self.lock
        ):  # Используем блокировку для синхронизации работы с ресурсом
            self._count = item  # Устанавливаем текущую задачу
            for _ in range(item):
                time.sleep(1)  # Задержка на 1 секунду для имитации работы
                self._count -= 1  # Уменьшаем счётчик по мере выполнения работы

        # Отправляем команду о завершении работы
        self.bus.put(Command(name="done"))

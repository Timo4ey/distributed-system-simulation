import abc
from multiprocessing.connection import Connection


# Абстрактный класс шины данных. Определяет интерфейс для взаимодействия с транспортным слоем.
class AbstractBus(abc.ABC):

    @abc.abstractmethod
    def put(self, obj, block=True, timeout=None):
        """
        Отправка данных в шину.

        :param obj: Объект для отправки.
        :param block: Указывает, будет ли операция блокирующей.
        :param timeout: Тайм-аут операции, если она блокирующая.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get(self, block=True, timeout=None):
        """
        Получение данных из шины.

        :param block: Указывает, будет ли операция блокирующей.
        :param timeout: Тайм-аут операции, если она блокирующая.
        """
        raise NotImplementedError()


# Базовый класс для реализации конкретных шин данных.
class BaseBus(AbstractBus):

    def __init__(self, transport):
        """
        Инициализация базовой шины с использованием переданного транспортного слоя.

        :param transport: Транспортный слой, предоставляющий методы передачи данных.
        """
        self._transport = transport


# Конкретная реализация шины данных, основанная на объекте Connection из multiprocessing.
class ConnectionBus(BaseBus):

    _transport: Connection  # Тип используемого транспортного слоя

    def __init__(self, transport: Connection):
        """
        Инициализация шины данных с использованием транспортного соединения.

        :param transport: Объект Connection для передачи данных.
        """
        super().__init__(transport)

    def get(self, block=True, timeout=None):
        """
        Получение данных из соединения.

        :param block: Не используется в данной реализации.
        :param timeout: Не используется в данной реализации.
        :return: Полученный объект.
        """
        return self._transport.recv()

    def put(self, obj, block=True, timeout=None):
        """
        Отправка данных через соединение.

        :param obj: Объект для отправки.
        :param block: Не используется в данной реализации.
        :param timeout: Не используется в данной реализации.
        """
        self._transport.send(obj)

    def pool(self, timeout: float | None = 0):
        """
        Проверяет наличие данных в соединении.

        :param timeout: Максимальное время ожидания данных.
        :return: True, если данные доступны для чтения, иначе False.
        """
        return self._transport.poll(timeout)

from multiprocessing import Process, Pipe, Queue
from multiprocessing.pool import ThreadPool
from collections import deque
import threading
import time
from typing import List

# Импорты пользовательских модулей и классов
from models import BusConnections, Command, CommandInfo, WorkerState
from bus import ConnectionBus
from workers import BaseWorker


def get_available_worker(workers: List[WorkerState]) -> WorkerState | None:
    # Фильтруем список работников,
    # выбирая первого свободного (с количеством заданий = 0)
    return next(filter(lambda w: w.jobs_count == 0, workers), None)


def bootstrap(
    WORKERS: List[Process],
    EVENT: threading.Event,
    STACK: deque,
    LOCK: threading.Lock,
) -> dict[str, WorkerState]:
    # Инициализация серверов и рабочих процессов
    workers: int = next(map(int, input("Введите количество серверов: ")))
    worker_map: dict[str, WorkerState] = dict()
    server_names = create_worker_name(workers)

    # Очередь задач ограничена количеством серверов
    global QUEUE
    QUEUE = Queue(maxsize=workers)

    # Создание процессов и привязка их через каналы связи (Pipes)
    for name in server_names:
        parent_con, child_con = Pipe()
        connections = BusConnections(
            parent_con=parent_con,
            child_con=child_con,
        )

        # Сохранение состояния каждого рабочего
        worker_map[name] = WorkerState(connections=connections, name=name)

        # Создание рабочего процесса и его запуск
        worker = Process(
            target=BaseWorker,
            args=(
                name,
                ConnectionBus(connections.child_con),
            ),
            daemon=True,
        )
        create_thread(
            worker_map[name]
        )  # Асинхронная привязка слушателя к процессу

        WORKERS.append(worker)
        worker.start()
        print(f"{name}: пусто")

    # Запуск основных асинхронных потоков: цикла событий и проверки статусов
    ThreadPool().apply_async(
        event_loop,
        args=(worker_map, EVENT, STACK, LOCK),
        error_callback=error_callback,
    )

    ThreadPool().apply_async(
        check_services_status,
        args=(worker_map, EVENT, STACK, LOCK),
        error_callback=error_callback,
    )
    return worker_map


def create_worker_name(worker_number: int) -> List[str]:
    # Генерация списка имен серверов в формате "Сервер 1", "Сервер 2", ...
    return [f"Сервер {i}" for i in range(1, worker_number + 1)]


def listen_worker(worker: WorkerState) -> WorkerState:
    # Слушаем команды от конкретного рабочего через Pipe
    command: CommandInfo | Command = worker.connections.parent_con.recv()

    # Обработка полученной команды от рабочего
    match command["name"]:
        case "done":  # Уведомление о завершении задания
            worker.jobs_count -= 1
            worker.total_work_time = 0

        case "info":  # Запрос на добавление информации в очередь
            QUEUE.put(command["body"])

    return worker


def check_services_status(
    worker_map: dict[str, WorkerState],
    event: threading.Event,
    STACK: deque,
    LOCK: threading.Lock,
    delay: float = 3.0,
):
    """Основной цикл проверки состояния серверов."""
    while True:
        time.sleep(delay)
        if event.is_set():
            return

        # Выполнение шагов проверки
        send_status_requests(worker_map)
        data = collect_worker_status(len(worker_map))
        res = format_server_status(data, STACK)
        handle = handle_queue_and_tasks(data, STACK)

        # Синхронный вывод информации
        with LOCK:
            print("\n".join(res))
            if handle:
                print("\n".join(handle))


def send_status_requests(worker_map: dict[str, WorkerState]):
    """Отправляет запросы статуса всем серверам."""
    for _, worker in worker_map.items():
        worker.connections.parent_con.send(Command(name="info"))


def collect_worker_status(worker_count: int) -> list:
    """Собирает статус всех серверов из очереди."""
    # Ожидаем, пока очередь заполнится
    while not QUEUE.full():
        pass

    # Извлечение статусов из очереди
    data = [QUEUE.get() for _ in range(worker_count)]
    return sorted(data, key=lambda x: x["name"])


def format_server_status(data: list, STACK: deque) -> list[str]:
    """Форматирует состояние серверов в удобный для вывода вид."""
    res = ["Состояние серверов:"]
    for u in data:
        status = (
            f"выполняет задание (осталось {u['number']} сек.)"
            if u["number"]
            else "пусто"
        )
        res.append(f"    {u['name']}: {status}")
    res.append(f"Очередь заданий: {[len(STACK)] if STACK else 'нет.'}")
    return res


def handle_queue_and_tasks(data: list, STACK: deque) -> list[str]:
    """Обрабатывает задачи в очереди и формирует логи выполнения."""
    handle = []
    read_for_next_task = None
    finish_number = None

    if STACK:
        # Найти сервер, который быстрее освободится, для следующего задания
        read_for_next_task = min(data, key=lambda x: x["number"])
        handle.append("\n\nОбработка:")
        name = read_for_next_task['name']
        handle.append(
            f" - {name} освобождается, задание из очереди направлено на {name}"
        )

    # Найти сервер, который скоро завершит выполнение
    finish_number = next(filter(lambda x: x["number"] <= 4, data), None)
    if finish_number and read_for_next_task:
        if finish_number["name"] != read_for_next_task["name"]:
            handle.append(f" - {finish_number['name']} завершает выполнение.")

    return handle


def create_thread(data):
    # Создание асинхронного слушателя для рабочего
    ThreadPool().apply_async(
        listen_worker,
        args=(data,),
        callback=create_thread,  # Рекурсивное восстановление потока при завершении
        error_callback=error_callback,
    )


def event_loop(
    worker_map: dict,
    EVENT: threading.Event,
    STACK: deque,
    LOCK: threading.Lock,
):
    # Основной цикл управления задачами
    while True:
        if EVENT.is_set():
            return

        # Проверка наличия свободного рабочего
        free_worker = get_available_worker(worker_map.values())
        if not free_worker:
            continue

        # Если есть задачи в стеке, передаем их на выполнение
        if STACK:
            number = STACK.popleft()
            free_worker.connections.parent_con.send(
                Command(name="add", body=number)
            )
            free_worker.jobs_count += 1
            with LOCK:
                print(
                    f"Задание с {number} секундами выполнения направлено на {free_worker.name}."
                )

        time.sleep(0.05)


def error_callback(*args, **kwargs):
    # Обработка ошибок в асинхронных задачах
    print("error_callback:", *args, **kwargs)


def run_server(
    worker_map: dict,
    STACK: deque,
    LOCK: threading.Lock,
):
    # Основной цикл приема пользовательских команд для добавления задач
    while True:
        inp = input("Команда: добавить ")
        try:
            num = next(map(int, inp), None)
            if num is None:
                continue

            # Добавление задания в стек
            STACK.append(num)
            w = get_available_worker(worker_map.values())
            if not w:
                with LOCK:
                    print(
                        f"Задание с {num} секундами выполнения добавлено в очередь."
                    )
        except ValueError:
            print("Ошибка ввода")

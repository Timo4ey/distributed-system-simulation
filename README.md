# Distributed System Simulation

This project is a simulation of a distributed system where multiple processes (servers) execute tasks. The goal is to showcase task distribution, queue management, and inter-process communication (IPC) without using external message brokers like Kafka or RabbitMQ.

[![Скриншот видео](media/screenshot.png)](media/2024-12-10%2022-05-12.mp4)


---

## Features

- **Task Queue Management**  
  Tasks can be added to a queue and are distributed to servers for execution. If all servers are busy, tasks remain in the queue until a server becomes available.

- **Optimal Task Distribution**  
  The system selects the server with the lowest workload (tasks with the shortest remaining execution time) to execute new tasks.

- **Inter-Process Communication (IPC)**  
  Uses Python's `multiprocessing` module with `Pipe` for bi-directional communication, enabling features like RPC to query server states.

- **Dynamic State Monitoring**  
  The system periodically checks and displays:
  - Current tasks and their remaining execution time for each server.
  - Pending tasks in the queue.
- **Asynchronous Processing**  
  Tasks are processed asynchronously using worker processes that simulate servers.

---

## How It Works

1. **Initialization**

   - The user specifies the number of servers to create.
   - Each server is initialized as a separate process and listens for commands using a communication bus.

2. **Task Addition**

   - The user inputs task durations (in seconds) via the console.
   - Tasks are either sent to idle servers or added to the task queue if no server is available.

3. **Task Execution**

   - Each server executes one task at a time, decrementing the remaining duration at 1-second intervals.
   - Once a task is completed, the server is marked as idle and ready for the next task.

4. **State Querying**
   - The system periodically queries all servers for their status and prints a summary of:
     - Servers currently executing tasks and their remaining durations.
     - Tasks waiting in the queue.

---

## Setup

### Prerequisites

- Python 3.10 or higher.
- Linux-based system (tested on Ubuntu).

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Timo4ey/distributed-system-simulation.git
   cd distributed-system-simulation
   ```
2. Install required dependencies (if any are listed in `requirements.txt`):
   ```bash
   pip install -r requirements.txt
   ```

---

## Usage

1. Start the simulation:

   ```bash
   make run
   ```

2. Follow the prompts:

   - Enter the number of servers during initialization.
   - Add tasks by specifying their execution durations.

3. Monitor the system:
   - View server states and queue status in real time.

---

## Code Structure

- **`main.py`**  
  Entry point for the application, orchestrating the system initialization and task management.
- **`workers.py`**  
  Contains the implementation of `BaseWorker`, which processes tasks and communicates with the main system.

- **`bus.py`**  
  Defines the `ConnectionBus` for IPC between the main system and worker processes.

- **`models.py`**  
  Contains data models used throughout the system, such as `WorkerState`, `Command`, and `CommandInfo`.

---

## Example

### Sample Interaction

```text
Введите количество серверов: 3
Команда: добавить
5
Задание с 5 секундами выполнения направлено на Сервер 1.
Состояние серверов:
    Сервер 1: выполняет задание (осталось 4 сек.)
    Сервер 2: пусто
    Сервер 3: пусто
Очередь заданий: нет.
```

---

## Potential Enhancements

1. **Dynamic Server Management**  
   Support for adding/removing servers during runtime.

2. **Advanced Scheduling Algorithms**  
   Consider factors like server performance for more efficient task distribution.

3. **Web Interface**  
   Replace console interaction with a web-based dashboard for monitoring and control.

4. **Logging**  
   Integrate `logging` for better debugging and system analytics.

---

## Author

This project was implemented by Timofey. It demonstrates core principles of distributed systems and inter-process communication using Python.

If you find this useful or have suggestions, feel free to create an issue or submit a pull request. 😊

---

## License

[MIT License](LICENSE)

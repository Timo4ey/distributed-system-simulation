#!/usr/bin/python3

from multiprocessing import Process
from collections import deque
import threading
from typing import List


from server import bootstrap, run_server


WORKERS: List[Process] = []
EVENT = threading.Event()


def main():
    STACK = deque()
    LOCK = threading.Lock()
    print("Добро пожаловать в симулятор распределенной системы.")
    worker_map = bootstrap(WORKERS, EVENT, STACK, LOCK)
    run_server(worker_map, STACK, LOCK)


if __name__ == "__main__":

    try:
        main()
    except KeyboardInterrupt:
        print("Trying to close opened processes...")
    finally:
        for pr in WORKERS:
            if pr.is_alive():
                # Try to terminate gracefully
                print(pr)
                pr.terminate()

                # Wait for the process to finish, but with a timeout
                pr.join(timeout=10)

        EVENT.set()

        print("All processes closed.")

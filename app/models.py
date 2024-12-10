from multiprocessing.connection import Connection
from typing import Any, Literal, Optional, TypedDict

from dataclasses import dataclass


class Command(TypedDict):
    name: Literal["add", "info"]
    body: Optional[Any] = None


class WorkerCommandBody(TypedDict):
    name: str
    number: int


class CommandInfo(Command):
    body: WorkerCommandBody


class ParentCon(Connection):
    pass


class ChildCon(Connection):
    pass


@dataclass
class BusConnections:
    parent_con: ParentCon
    child_con: ChildCon


@dataclass
class WorkerState:
    connections: BusConnections
    name: str
    jobs_count: int = 0
    total_work_time: int = 0

from contextvars import ContextVar
from typing import Optional


class _Sentinel:
    pass


_NO_SINK = _Sentinel()


current_sink: ContextVar = ContextVar("current_sink", default=_NO_SINK)
current_node: ContextVar = ContextVar("current_node", default=None)
current_step: ContextVar = ContextVar("current_step", default=None)


def set_sink(sink) -> None:
    current_sink.set(sink)


def get_sink():
    sink = current_sink.get()
    return None if sink is _NO_SINK else sink


def set_node(name: Optional[str]) -> None:
    current_node.set(name)


def get_node() -> Optional[str]:
    return current_node.get()


def set_step(step_index: Optional[int]) -> None:
    current_step.set(step_index)


def get_step() -> Optional[int]:
    return current_step.get()



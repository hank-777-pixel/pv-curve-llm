from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
import uuid

from agent.output.context import get_sink, get_node, get_step
from agent.output.models import ProgressEvent


def _emit_event(event_type: str, text: str | None = None, level: str = "info") -> None:
    sink = get_sink()
    if not sink:
        return
    sink.emit(
        ProgressEvent(
            id=f"evt_{uuid.uuid4().hex[:12]}",
            type=event_type,  # type: ignore
            text=text,
            node=get_node(),
            step=get_step(),
            ts=datetime.now(),
            level=level,  # type: ignore
        )
    )


def info(text: str) -> None:
    _emit_event("info", text, level="info")


def answer(text: str) -> None:
    _emit_event("answer", text, level="info")


@contextmanager
def spinner(text: str):
    sink = get_sink()
    if not sink:
        def _noop(_text: str):
            pass
        yield _noop
        return
    with sink.spinner(text) as update:
        yield update



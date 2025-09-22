from __future__ import annotations

from contextlib import contextmanager
from typing import Callable, List, Optional
from datetime import datetime
import uuid

from agent.output.models import ProgressEvent
from agent.output.context import get_node, get_step


class BaseSink:
    def emit(self, event: ProgressEvent) -> None:
        raise NotImplementedError

    @contextmanager
    def spinner(self, text: str):
        spinner_id = f"sp_{uuid.uuid4().hex[:8]}"
        self.emit(
            ProgressEvent(
                id=f"evt_{uuid.uuid4().hex[:12]}",
                type="spinner_start",
                text=text,
                node=get_node(),
                step=get_step(),
                ts=datetime.now(),
                spinner_id=spinner_id,
            )
        )

        def update(new_text: str):
            self.emit(
                ProgressEvent(
                    id=f"evt_{uuid.uuid4().hex[:12]}",
                    type="spinner_update",
                    text=new_text,
                    node=get_node(),
                    step=get_step(),
                    ts=datetime.now(),
                    spinner_id=spinner_id,
                )
            )

        try:
            yield update
        finally:
            self.emit(
                ProgressEvent(
                    id=f"evt_{uuid.uuid4().hex[:12]}",
                    type="spinner_end",
                    node=get_node(),
                    step=get_step(),
                    ts=datetime.now(),
                    spinner_id=spinner_id,
                )
            )


class MemorySink(BaseSink):
    def __init__(self):
        self._events: List[ProgressEvent] = []

    def emit(self, event: ProgressEvent) -> None:
        self._events.append(event)

    def get_events(self) -> List[dict]:
        # Convert datetimes to ISO strings and include compatibility keys
        events = []
        for e in self._events:
            d = e.model_dump()
            d["ts"] = e.ts.isoformat()
            # Back-compat for previous web payloads
            if "text" in d and d.get("text") is not None:
                d["message"] = d.get("text")
            d["timestamp"] = d["ts"]
            events.append(d)
        return events

    def clear(self) -> None:
        self._events = []


class CompositeSink(BaseSink):
    def __init__(self, sinks: List[BaseSink]):
        self._sinks = sinks

    def emit(self, event: ProgressEvent) -> None:
        for sink in self._sinks:
            sink.emit(event)

    @contextmanager
    def spinner(self, text: str):
        managers = [sink.spinner(text) for sink in self._sinks]
        exits = []
        try:
            updates = [mgr.__enter__() for mgr in managers]

            def update(new_text: str):
                for fn in updates:
                    fn(new_text)

            yield update
        finally:
            for mgr in managers:
                mgr.__exit__(None, None, None)


class TerminalSink(BaseSink):
    def __init__(self):
        from rich.console import Console
        from rich.markdown import Markdown
        from yaspin import yaspin
        self.console = Console()
        self.Markdown = Markdown
        self.yaspin = yaspin

    def emit(self, event: ProgressEvent) -> None:
        if event.type == "info":
            self.console.print(f"[grey50]{event.text}")
        elif event.type == "answer":
            self.console.print(self.Markdown((event.text or "").strip()))
        elif event.type in {"spinner_start", "spinner_update", "spinner_end"}:
            # Spinner lifecycle handled by spinner contextmanager below
            pass
        elif event.type == "error":
            self.console.print(f"[red]{event.text}")

    @contextmanager
    def spinner(self, text: str):
        with self.yaspin(text=text, color="white") as sp:
            def update(new_text: str):
                sp.text = new_text
            yield update



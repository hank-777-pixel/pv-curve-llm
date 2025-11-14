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



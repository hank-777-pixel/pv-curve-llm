from rich.console import Console
from agent.output.context import set_sink, get_sink
from agent.output.sinks import TerminalSink
from agent.output.router import info as _info, answer as _answer, spinner as _spinner

console = Console()
_line = "-" * console.width

_sink = get_sink()
if _sink is None:
    set_sink(TerminalSink())

def divider():
    console.print(_line)

def info(text: str):
    _info(text)

def answer(text: str):
    _answer(text)

def spinner(text: str):
    return _spinner(text)

from contextlib import contextmanager
from rich.console import Console
from rich.markdown import Markdown
from yaspin import yaspin

console = Console()
_line = "-" * console.width

def divider():
    console.print(_line)


def info(text: str):
    console.print(f"[grey50]{text}")


def answer(text: str):
    console.print(Markdown(text.strip()))


@contextmanager
def spinner(text: str):
    # grey spinner with dynamic text updates
    with yaspin(text=text, color="white") as sp:
        def _update(new_text: str):
            sp.text = new_text
        yield _update

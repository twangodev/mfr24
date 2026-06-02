from __future__ import annotations

import typer
from rich.console import Console

stdout = Console()
stderr = Console(stderr=True)


def fail(message: str, *, code: int = 1) -> typer.Exit:
    stderr.print(f"[bold red]error[/] {message}")
    return typer.Exit(code)

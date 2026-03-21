"""Rich-based console utilities: colors, progress, tables, prompts."""

from __future__ import annotations

import os

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from rich.table import Table
from rich.theme import Theme

# ---------------------------------------------------------------------------
# Theme & Console singleton
# ---------------------------------------------------------------------------

AION_THEME = Theme(
    {
        "info": "cyan",
        "success": "bold green",
        "warning": "bold yellow",
        "error": "bold red",
        "header": "bold magenta",
        "muted": "dim",
        "path": "underline blue",
    }
)


def _make_console() -> Console:
    no_color = os.environ.get("NO_COLOR") is not None
    return Console(theme=AION_THEME, no_color=no_color, highlight=False)


console = _make_console()


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------


def header(text: str) -> None:
    """Print a styled header."""
    console.print(f"\n[header]{text}[/header]")


def info(text: str) -> None:
    console.print(f"[info]{text}[/info]")


def success(text: str) -> None:
    console.print(f"[success]✓ {text}[/success]")


def warning(text: str) -> None:
    console.print(f"[warning]⚠ {text}[/warning]")


def error(text: str) -> None:
    console.print(f"[error]✗ {text}[/error]")


def muted(text: str) -> None:
    console.print(f"[muted]{text}[/muted]")


def path_display(text: str) -> None:
    console.print(f"[path]{text}[/path]")


def banner(title: str, subtitle: str = "") -> None:
    """Print a styled banner box."""
    content = f"[bold]{title}[/bold]"
    if subtitle:
        content += f"\n[muted]{subtitle}[/muted]"
    console.print(Panel(content, border_style="magenta", padding=(0, 2)))


# ---------------------------------------------------------------------------
# Interactive prompts
# ---------------------------------------------------------------------------


def confirm(prompt: str, default: bool = False) -> bool:
    """Ask a yes/no question. Returns boolean."""
    suffix = "[Y/n]" if default else "[y/N]"
    try:
        answer = console.input(f"{prompt} {suffix} ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        console.print()
        return default
    if not answer:
        return default
    return answer in ("y", "yes")


def ask(prompt: str, default: str = "") -> str:
    """Ask for text input."""
    suffix = f" [{default}]" if default else ""
    try:
        answer = console.input(f"{prompt}{suffix}: ").strip()
    except (EOFError, KeyboardInterrupt):
        console.print()
        return default
    return answer or default


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------


def status_table(title: str, checks: list[tuple[str, bool, str]]) -> None:
    """Print a diagnostic checklist table.

    Args:
        title: Table title.
        checks: List of (label, passed, detail) tuples.
    """
    table = Table(title=title, show_header=True, header_style="bold")
    table.add_column("Status", width=4, justify="center")
    table.add_column("Check", min_width=20)
    table.add_column("Detail", style="muted")

    for label, passed, detail in checks:
        icon = "[success]✓[/success]" if passed else "[error]✗[/error]"
        table.add_row(icon, label, detail)

    console.print(table)


def file_table(title: str, rows: list[tuple[str, str, str]]) -> None:
    """Print a file operation table.

    Args:
        title: Table title.
        rows: List of (file, action, detail) tuples.
    """
    table = Table(title=title, show_header=True, header_style="bold")
    table.add_column("File", style="path")
    table.add_column("Action", min_width=10)
    table.add_column("Detail", style="muted")

    for file, action, detail in rows:
        table.add_row(file, action, detail)

    console.print(table)


# ---------------------------------------------------------------------------
# Progress bars
# ---------------------------------------------------------------------------


def download_progress() -> Progress:
    """Create a progress bar suitable for file downloads."""
    return Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=console,
    )


def step_progress(total: int, description: str = "Progress") -> Progress:
    """Create a simple step-based progress bar."""
    return Progress(
        TextColumn("[bold]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        console=console,
    )


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


def install_report(
    *,
    title: str,
    created: list[str],
    updated: list[str],
    skipped: list[str],
    warnings: list[str] | None = None,
) -> None:
    """Print an install/init summary report."""
    rows: list[tuple[str, str, str]] = []
    for f in created:
        rows.append((f, "[success]created[/success]", ""))
    for f in updated:
        rows.append((f, "[info]updated[/info]", ""))
    for f in skipped:
        rows.append((f, "[muted]skipped[/muted]", "exists"))

    if rows:
        file_table(title, rows)

    summary_parts = []
    if created:
        summary_parts.append(f"[success]{len(created)} created[/success]")
    if updated:
        summary_parts.append(f"[info]{len(updated)} updated[/info]")
    if skipped:
        summary_parts.append(f"[muted]{len(skipped)} skipped[/muted]")

    console.print(f"\nSummary: {', '.join(summary_parts)}")

    if warnings:
        for w in warnings:
            warning(w)

import asyncio
from typing import Annotated

import typer

from gwscan2.parsing import parse_page_range
from gwscan2.workflows.battlefield_flow import run_test_battlefield_scan
from gwscan2.workflows.test_auth import run_test_auth_flow

app = typer.Typer(help="GateWa.rs scanning tools")


@app.callback()
def main() -> None:
    """CLI entrypoint for GateWa.rs tools."""


@app.command("test-auth")
def test_auth_flow_command() -> None:
    asyncio.run(run_test_auth_flow())



@app.command("test-battlefield")
def test_battlefield_scan_command(
    page_range: Annotated[
        str,
        typer.Argument(help="Page range to scan, for example 1001:2000."),
    ],
) -> None:
    asyncio.run(run_test_battlefield_scan(page_range=parse_page_range(page_range)))

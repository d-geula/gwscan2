import asyncio
from typing import Annotated

import typer

from gwscan2.parsing import parse_page_range
from gwscan2.workflows.battlefield_flow import run_test_battlefield_scan


app = typer.Typer(help="GateWa.rs scanning tools")
scan_app = typer.Typer(help="Scan commands")
app.add_typer(scan_app, name="scan")


# @app.callback()
# def main() -> None:
#     """CLI entrypoint for GateWa.rs tools."""


#TODO: implement flag for headless/headed mode
@scan_app.command("battlefield")
def test_battlefield_scan_command(
    page_range: Annotated[
        str,
        typer.Argument(help="Page range to scan, for example 1001:2000."),
    ],
) -> None:
    asyncio.run(run_test_battlefield_scan(page_range=parse_page_range(page_range)))

import asyncio

import typer

from gwscan2.workflows.test_auth import test_auth_flow

app = typer.Typer(help="GateWa.rs scanning tools")


@app.callback()
def main() -> None:
    """CLI entrypoint for GateWa.rs tools."""


@app.command("test-auth")
def test_auth_flow_command() -> None:
    asyncio.run(test_auth_flow())

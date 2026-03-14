import asyncio

import typer

from workflows.test_auth import test_auth_flow

app = typer.Typer(help="GateWa.rs scanning tools")

@app.command("Test Auth Flow")
def test_auth_flow_command():
    asyncio.run(test_auth_flow())
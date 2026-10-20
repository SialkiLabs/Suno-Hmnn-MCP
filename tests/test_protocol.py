import json
import os
import subprocess
import sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def test_import_has_no_stdout_or_storage_side_effects(tmp_path):
    output = tmp_path / "unused"
    env = {
        **os.environ,
        "SUNO_OUTPUT_DIR": str(output),
        "SUNO_DATABASE_PATH": str(output / "db"),
    }
    result = subprocess.run(
        [sys.executable, "-c", "import server; print('IMPORT_OK')"],
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )
    assert result.stdout.strip() == "IMPORT_OK" and not output.exists()


async def test_stdio_initialization_and_tool_list():
    server = Path(__file__).resolve().parents[1] / "server.py"
    params = StdioServerParameters(
        command=sys.executable, args=[str(server)], env=dict(os.environ)
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            names = {tool.name for tool in result.tools}
            assert len(names) == 10 and "suno_generate" in names
            download = next(
                tool for tool in result.tools if tool.name == "suno_download_file"
            )
            assert download.inputSchema["properties"]["file_format"]["enum"] == [
                "wav",
                "mp3",
            ]

            library = await session.call_tool("suno_list_local_library", {"limit": 1})
            assert not library.isError
            invalid = await session.call_tool("suno_list_local_library", {"limit": -1})
            assert invalid.isError

"""File upload — bypass the LLM context window to get files onto the server.

The most practical use of MCP Apps: letting users upload files directly to
the server without pushing bytes through the model's context. The LLM asks
the user to upload, the user drops files, clicks Upload, and the server
stores them. The LLM can then work with the files through backend tools.

Usage:
    uv run python file_upload_server.py
"""

from __future__ import annotations

import base64
from datetime import datetime

from prefab_ui.actions import SetState, ShowToast
from prefab_ui.actions.mcp import CallTool
from prefab_ui.app import PrefabApp
from prefab_ui.components import (
    H3,
    Badge,
    Button,
    Card,
    CardContent,
    CardFooter,
    CardHeader,
    Column,
    DropZone,
    Muted,
    Row,
    Separator,
    Small,
    Text,
)
from prefab_ui.components.control_flow import Else, ForEach, If
from prefab_ui.rx import ERROR, RESULT, STATE, Rx

from fastmcp import FastMCP, FastMCPApp

# ---------------------------------------------------------------------------
# In-memory file store
# ---------------------------------------------------------------------------

_files: dict[str, dict] = {}

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastMCPApp("Files")


@app.tool()
def store_files(files: list[dict]) -> list[dict]:
    """Store uploaded files. Receives file objects with name, size, type, data (base64)."""
    for f in files:
        _files[f["name"]] = {
            "name": f["name"],
            "size": f["size"],
            "type": f["type"],
            "data": f["data"],
            "uploaded_at": datetime.now().isoformat(timespec="seconds"),
        }
    return _file_summaries()


@app.tool(model=True)
def list_files() -> list[dict]:
    """List all uploaded files with metadata."""
    return _file_summaries()


@app.tool(model=True)
def read_file(name: str) -> dict:
    """Read an uploaded file's contents by name."""
    if name not in _files:
        available = list(_files.keys())
        raise ValueError(f"File {name!r} not found. Available: {available}")
    entry = _files[name]
    result = {
        "name": entry["name"],
        "size": entry["size"],
        "type": entry["type"],
        "uploaded_at": entry["uploaded_at"],
    }
    if entry["type"].startswith("text/") or entry["name"].endswith(
        (".csv", ".json", ".txt", ".md", ".py", ".yaml", ".yml", ".toml")
    ):
        try:
            result["content"] = base64.b64decode(entry["data"]).decode("utf-8")
        except (UnicodeDecodeError, Exception):
            result["content_base64"] = entry["data"][:200] + "..."
    else:
        result["content_base64"] = entry["data"][:200] + "..."
    return result


@app.ui()
def file_manager() -> PrefabApp:
    """Upload and manage files. Drop files here to send them to the server."""
    with Card(css_class="max-w-2xl mx-auto") as view:
        with CardHeader():
            with Row(gap=2, align="center"):
                H3("File Upload")
                with If(STATE.stored.length()):
                    Badge(STATE.stored.length(), variant="secondary")

        with CardContent():
            with Column(gap=4):
                Muted(
                    "Drop files to upload them to the server. "
                    "The model can then read and analyze them "
                    "without using the context window."
                )

                DropZone(
                    name="pending",
                    icon="inbox",
                    label="Drop files here",
                    description="Any file type, up to 10MB",
                    multiple=True,
                    max_size=10 * 1024 * 1024,
                )

                # Show pending files
                with If(STATE.pending.length()):
                    with Column(gap=2):
                        with ForEach("pending") as (i, item):
                            with Row(gap=2, align="center"):
                                with Column(gap=0):
                                    Small(item.name)
                                    Muted(f"{item.type} · {item.size} bytes")

                        Button(
                            "Upload to Server",
                            on_click=CallTool(
                                "store_files",
                                arguments={"files": Rx("pending")},
                                on_success=[
                                    SetState("stored", RESULT),
                                    SetState("pending", []),
                                    ShowToast("Files uploaded!", variant="success"),
                                ],
                                on_error=ShowToast(ERROR, variant="error"),
                            ),
                        )

                # Show uploaded files
                with If(STATE.stored.length()):
                    Separator()
                    Text("Uploaded", css_class="font-medium text-sm")
                    with ForEach("stored") as f:
                        with Row(gap=2, align="center", css_class="justify-between"):
                            with Column(gap=0):
                                Small(f.name)
                                Muted(f.uploaded_at)
                            with Row(gap=2):
                                Badge(f.type, variant="secondary")
                                Badge(f.size_display, variant="outline")

        with CardFooter():
            with Row(align="center", css_class="w-full"):
                with If(STATE.stored.length()):
                    Muted(
                        f"{STATE.stored.length()}"
                        f" {STATE.stored.length().pluralize('file')} on server"
                    )
                with Else():
                    Muted("No files uploaded yet")

    return PrefabApp(view=view, state={"pending": [], "stored": _file_summaries()})


def _file_summaries() -> list[dict]:
    summaries = []
    for entry in _files.values():
        size = entry["size"]
        if size < 1024:
            size_display = f"{size} B"
        elif size < 1024 * 1024:
            size_display = f"{size / 1024:.1f} KB"
        else:
            size_display = f"{size / (1024 * 1024):.1f} MB"
        summaries.append(
            {
                "name": entry["name"],
                "type": entry["type"],
                "size_display": size_display,
                "uploaded_at": entry["uploaded_at"],
            }
        )
    return summaries


mcp = FastMCP("File Upload Server", providers=[app])

if __name__ == "__main__":
    mcp.run()

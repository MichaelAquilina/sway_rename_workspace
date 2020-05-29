import os
import re
import shutil
from typing import List

from i3ipc import Connection, Event

GLYPH_MAP = {
    "kitty": "" ,
    "Monitor": "",
    "firefox": "",
    "rhythmbox": "",
    "Spotify": "",
    "Network": "  ",
    "Calculator": "  ",
    "Default": "  ",
}

def rename_workspaces(i3, event):
    for workspace in i3.get_tree().workspaces():
        set_workspace_name(i3, workspace)


def set_workspace_name(i3, workspace):
    icons = set()
    for node in workspace.leaves():
        # X windows
        if node.app_id is None:
            key = node.ipc_data["window_properties"]["class"]
        else:
            key = node.app_id

        print(key)

        if key in GLYPH_MAP:
            icons.add(GLYPH_MAP[key])


    old = workspace.name
    new = f"{workspace.num} " + " ".join(sorted(icons))

    i3.command(f"rename workspace '{old}' to '{new}'")


def main():
    i3 = Connection()

    i3.on(Event.WINDOW_NEW, rename_workspaces)
    i3.on(Event.WINDOW_CLOSE, rename_workspaces)
    i3.on(Event.WINDOW_MOVE, rename_workspaces)
    i3.main()


if __name__ == "__main__":
    main()

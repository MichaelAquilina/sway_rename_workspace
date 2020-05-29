import os
import re
import shutil
from typing import List

from i3ipc import Connection, Event

ICON_MAP = {
    "kitty": "",
    "firefox": "",
}


def get_data_dirs() -> List[str]:
    """
    Returns list of application data dirs that contain .desktop files.
    List is ordered by priority in descending order
    """
    xdg_data_dirs = os.environ["XDG_DATA_DIRS"].split(":")

    # local applications directory should take highest priority
    result = [os.path.expanduser("~/.local/share/applications")]
    for path in xdg_data_dirs:
        result.append(os.path.join(path, "applications"))

    return result


def command_exists(command: str) -> bool:
    return shutil.which(command) != None


def get_all_desktop_entries(data_dirs: List[str], key_name: str) -> dict:
    GLYPH_MAP = {
        "TerminalEmulator": "  ",
        "Monitor": "  ",
        "WebBrowser": "  ",
        "InstantMessaging": "  ",
        "Game": "  ",
        "Security": "  ",
        "Graphics": "  ",
        "System": "  ",
        "TextEditor": "  ",
        "Player": "  ",
        "Network": "  ",
        "Calculator": "  ",
        "FileManager": "  ",
        "Office": "  ",
        "Default": "  ",
    }

    desktop_entries = {}
    for directory in data_dirs:
        for root, dirs, files in os.walk(directory):
            for entry in files:
                if not entry.endswith(".desktop"):
                    continue

                desktop = get_desktop(os.path.join(root, entry))

                name = desktop.get("Name", "")
                no_display = desktop.get("NoDisplay") == "true"
                try_exec = desktop.get("TryExec")
                desktop_type = desktop.get("Type", "Application")
                terminal = desktop.get("Terminal") == "true"
                categories = desktop.get("Categories", "").split(";")

                if key_name not in desktop:
                    continue

                index = desktop[key_name]

                if try_exec and not command_exists(try_exec):
                    continue

                # If name has already been populated, then it
                # should have the highest priority
                if name in desktop_entries:
                    continue

                # No display means it should never show in launchers
                if no_display or not name:
                    continue

                # priority of glyph should start from the
                # end of the category list
                for category in categories[::-1]:
                    if category in GLYPH_MAP:
                        glyph = category
                        break
                else:
                    glyph = "Default"

                desktop["glyph"] = GLYPH_MAP[glyph]
                desktop_entries[index] = desktop
    return desktop_entries


def get_desktop(path: str) -> dict:
    required_fields = [
        "Name",
        "Categories",
        "Exec",
        "TryExec",
        "Terminal",
        "NoDisplay",
        "Comment",
        "Type",
        "_path"
    ]

    # It's actually faster reading data all at once
    # Then iterating through the lines and breaking early
    with open(path, "r") as fp:
        data = fp.readlines()

    # Include for potential debugging purposes
    result = {"_path": path}

    for line in data:
        # Finding any new section means we should stop
        match = re.match(r"\[(?P<name>.+)\]", line)

        if match and match.group("name") != "Desktop Entry":
            break

        if "=" not in line:
            continue

        tokens = line.split("=")
        field = tokens[0]
        value = "=".join(tokens[1:])

        # Only bother populating the fields that matter
        if True or field in required_fields:
           result[field] = value.rstrip("\n")

        if result.keys() == required_fields:
            break

    return result


# These are special freedesktop defined parameters which we need to remove
# as we are not launching them in any special way (e.g. using a target file)
# see https://developer.gnome.org/desktop-entry-spec/#exec-variables
FIELD_CODES = [
    "%s", "%u", "%U", "%f", "%F", "%d", "%D", "%n", "%N", "%i", "%c", "%k", "%v", "%m"
]


def get_executable(value: str) -> List[str]:
    result = []
    for token in value.split(" "):
        if token not in FIELD_CODES:
            result.append(token.strip('"'))
    return result

def rename_workspaces(i3, event):
    if event.change in ("new", "close"):

        data_dirs = get_data_dirs()
        desktop_entries = get_all_desktop_entries(data_dirs, "TryExec")

        con = i3.get_tree().find_focused()

        workspace = con.workspace()

        icons = set()
        for node in workspace.leaves():
            if node.app_id in desktop_entries:
                icons.add(desktop_entries.get(node.app_id)["glyph"])

        old = workspace.name
        new = f"{workspace.num} " + " ".join(sorted(icons))

        i3.command(f"rename workspace '{old}' to '{new}'")


def main():
    i3 = Connection()
    i3.on(Event.WINDOW_NEW, rename_workspaces)
    i3.on(Event.WINDOW_CLOSE, rename_workspaces)
    i3.main()


if __name__ == "__main__":
    main()

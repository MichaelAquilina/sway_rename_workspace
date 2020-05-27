from i3ipc import Connection, Event

ICON_MAP = {
    "kitty": "",
    "firefox": "",
}


def rename_workspaces(i3, event):
    if event.change in ("new", "close"):
        con = i3.get_tree().find_focused()

        workspace = con.workspace()

        icons = {ICON_MAP[l.app_id] for l in workspace.leaves() if l.app_id in ICON_MAP}

        old = workspace.name
        new = f"{workspace.num} " + " ".join(icons)

        i3.command(f"rename workspace '{old}' to '{new}'")


def main():
    i3 = Connection()
    i3.on(Event.WINDOW_NEW, rename_workspaces)
    i3.on(Event.WINDOW_CLOSE, rename_workspaces)
    i3.main()


if __name__ == "__main__":
    main()

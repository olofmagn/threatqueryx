import tkinter as tk
import sys

from utils.configuration import resolve_platform_and_templates, choose_mode

from .cli import QueryCli
from .gui import QueryGui

"""
Main runner
"""

VERSION = "1.0.0"

BANNER = rf"""
  _   _                    _
 | |_| |__  _ __ ___  __ _| |_ __ _ _   _  ___ _ __ _   ___  __
 | __| '_ \| '__/ _ \/ _` | __/ _` | | | |/ _ \ '__| | | \ \/ /
 | |_| | | | | |  __/ (_| | || (_| | |_| |  __/ |  | |_| |>  <
  \__|_| |_|_|  \___|\__,_|\__\__, |\__,_|\___|_|   \__, /_/\_\
                                 |_|                |___/

Welcome to the application! 
Enjoy using the app, and feel free to share any feature requests or feedback!
Version {VERSION} olofmagn
"""


def main():
    print(BANNER)

    mode = choose_mode()
    platform = None

    if mode is None or mode.lower() == "quit":
        print("Goodbye")
        sys.exit(1)

    platform, templates, base_queries = resolve_platform_and_templates(mode, platform)

    if mode == "cli":
        cli = QueryCli(platform, templates, base_queries)
        cli.build_query_for_cli()
    else:
        root = tk.Tk()
        QueryGui(root)
        root.mainloop()


if __name__ == "__main__":
    main()

"""
A simple program that generates a search query based on a given list.

Author: Olof Magnusson
Date: 2025-06-18
"""

import tkinter as tk

from utils.utils import parse_args
from utils.utils import resolve_platform_and_templates
from utils.utils import choose_mode

from .cli import QueryCli
from .gui import QueryGui

BANNER= r"""
  _   _                    _
 | |_| |__  _ __ ___  __ _| |_ __ _ _   _  ___ _ __ _   ___  __
 | __| '_ \| '__/ _ \/ _` | __/ _` | | | |/ _ \ '__| | | \ \/ /
 | |_| | | | | |  __/ (_| | || (_| | |_| |  __/ |  | |_| |>  <
  \__|_| |_|_|  \___|\__,_|\__\__, |\__,_|\___|_|   \__, /_/\_\
                                 |_|                |___/

Welcome to the application! 
Enjoy using the app, and feel free to share any feature requests or feedback!
Designed by Olof Magnusson (olofmagn)
"""

def main():
    print(BANNER)
    # Check whether we should use cli or gui based on args (default gui)
    args = parse_args()
    mode= choose_mode()
    platform = None
    
    # Early exit
    if mode in ("quit", None):
        sys.exit(1)

    platform, templates = resolve_platform_and_templates(mode, platform)
    
    if mode == "cli":
        cli_test = QueryCli(platform, templates)
        cli_test.build_query_for_cli()
    else:
        root = tk.Tk()
        app = QueryGui(root)
        app.platform_var.set(platform.upper())
        app.load_templates_for_platform(platform)
        root.mainloop()

if __name__ == "__main__":
    main()

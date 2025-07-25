import ipaddress
import os
import re
import sys
from typing import Dict, Any, Literal, Tuple, Optional

import questionary
import yaml

from utils.ui_constants import DEFAULT_ENCODING, VALID_PLATFORMS

"""
Configuration utility
"""


def load_templates(platform: str) -> Dict[str, Any]:
    """
    Loads templates for the specified SIEM platform

    Args:
    - platform (str): The SIEM platform name (e.g., 'qradar', 'elastic', 'defender')

    Returns:
    - Dict[str, Any]: Parsed YAML template as a dictionary
    """

    if platform.lower() == "quit":
        print("Goodbye")
        sys.exit(1)

    file_path = os.path.join("templates", f"{platform.lower()}.yaml")
    try:
        with open(file_path, "r", encoding=DEFAULT_ENCODING) as f:
            templates = yaml.safe_load(f)
            return templates
    except FileNotFoundError:
        print(f"File not found. Check if you provided correct {file_path}")
        sys.exit(1)
    except IOError as e:
        print(f"I/O Error occurred when reading {file_path}: {e}")
        sys.exit(1)


def validate(value: str, val_type: Optional[str]) -> Tuple[bool, str]:
    """
    Validates a given value against a specific type

    Args:
    - value (str): The value to validate (e.g., IP address or port)
    - val_type (Optional[str]): The type to validate against (e.g., 'ip', 'port', 'domain')

    Returns:
    - Tuple[bool, str]: Whether the value is valid with a result or error message
    """

    match val_type:
        case "ip":
            try:
                ipaddress.ip_address(value)
                return True, ""
            except ValueError:
                return False, "Invalid IP Address"
        case "integer":
            try:
                int(value)
                return True, ""
            except ValueError:
                return False, "Must be an integer"
        case _:
            return True, ""


def resolve_platform_and_templates(
    mode: Literal["cli", "gui"], platform: Optional[str]
) -> Tuple[str, Optional[Dict[str, Any]], Optional[Dict[str, str]]]:
    """
    Resolves platform and templates given the mode and platform

    Args:
    - mode (Literal["cli", "gui"]): The interface mode (cli or gui)
    - platform (Optional[str]): The platform to use, e.g., 'qradar', 'elastic' or 'defender'

    Returns:
    - Tuple[str, Optional[Dict[str, Any]], Optional[Dict[str, str]]]: The platform name, templates, and base_queries
    """

    if mode == "cli":
        choices = [
            questionary.Choice(
                title=f"{name} - {meta.get('description', 'no description')}",
                value=name,
            )
            for name, meta in VALID_PLATFORMS.items()
        ] + [questionary.Choice("Quit", value="quit")]

        platform = questionary.select(
            "Choose a platform to use:", choices=choices
        ).ask()

        if platform in ("Quit", None):
            return "Quit", None, None  # Let main.py handle the exit

        try:
            config = load_templates(platform)
            base_queries = config.get("base_queries", {})
            templates = {k: v for k, v in config.items() if k != "base_queries"}
            return platform, templates, base_queries
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    else:
        platform = platform or "qradar"
        return platform, None, None


def choose_mode() -> Optional[str]:
    """
    Choose between GUI and CLI mode

    Returns:
    - Optional[str]: The chosen mode, or None if quit is selected
    """

    mode = questionary.select(
        "Choose interface mode:",
        choices=[
            questionary.Choice("CLI (terminal)", value="cli"),
            questionary.Choice("GUI (graphical)", value="gui"),
            questionary.Choice("Quit", value="quit"),
        ],
    ).ask()

    return mode  # Let main.py handle quit logic


def normalize_lookback(lookback: str, platform: str) -> Optional[str]:
    """
    Normalizes lookback values for different platforms

    Args:
    - lookback (str): The string value to transform to correct format
    - platform (str): The platform name for format determination

    Returns:
    - Optional[str]: A lookback value in the correct format, or None if invalid
    """

    lookback = lookback.strip().lower()
    match = re.match(
        r"(\d+)\s*(minutes?|hours?|days?|min|m|h|d)", lookback, re.IGNORECASE
    )

    if not match:
        return None

    value, unit = match.groups()
    value = int(value)

    if value <= 0:
        return None

    is_defender_or_elastic = platform in ("defender", "elastic")

    match unit:
        case "minute" | "minutes" | "min" | "m":
            return f"{value}m" if is_defender_or_elastic else f"{value} MINUTES"
        case "hour" | "hours" | "h":
            return f"{value}h" if is_defender_or_elastic else f"{value} HOURS"
        case "day" | "days" | "d":
            return f"{value}d" if is_defender_or_elastic else f"{value} DAYS"
        case _:
            return None

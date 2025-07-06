
"""
Utils functions
"""

import os
import sys
import yaml
import ipaddress
import re
import questionary
from typing import Dict, Literal

VALID_PLATFORMS = {
    "defender": {"description": "Microsoft Defender for Endpoint"},
    "elastic": {"description": "Elastic SIEM"},
    "qradar": {"description": "IBM QRadar"}
}

def load_templates(platform: str) -> Dict[str,any]:

    """
    Loads templates for the specified SIEM platform.

    Args:
        platform (str): The SIEM platform name (e.g., 'qradar', 'elastic', 'defender').

    Returns:
        dict: Parsed YAML template as a dictionary.
    """
    file_path = os.path.join("templates", f"{platform.lower()}.yaml")
    try:
        with open(file_path, "r", encoding='utf-8') as f:
            templates = yaml.safe_load(f)
            return templates
    except FileNotFoundError:
        print(f"File not found. Check if you provided correct {file_path}")
        sys.exit(1)
    except IOError as e:
        print(f"I/O Error occured when reading {file_path}")
        sys.exit(1)

def validate(value: str, val_type: str) -> tuple[bool, str]:

    """
    Validates a given value against a specific type

    Args:
    - value (str):  The value to validate (e.g., IP address or port.
    - val_type (str): The type to validate against (e.g., 'ip', 'port', 'domain')

    Returns:
    - tuple[bool,str]: whether the value is valid with a result or error.
    """
    if val_type == "ip":
        try:
            ipaddress.ip_address(value)
            return True, ""
        except ValueError:
            return False, "Invalid IP Address"
    elif val_type == "integer":
        return value.isdigit(), "Must be an integer"
    return True, ""

def parse_args():

    """
    Returns:
    - str: A parsed mode and platform string to determine use.
    """
    mode = "gui"
    platform = None

    for arg in sys.argv[1:]:
        arg_l = arg.lower()
        if arg_l == "cli":
            mode = "cli"
        elif arg_l in VALID_PLATFORMS:
            platform = arg_l

    return mode, platform

def resolve_platform_and_templates(mode: Literal["cli", "gui"], platform: str) -> str:

    """
    Resolves platform and templates given the platform

    Args:
    - mode (str): The value of mode (cli or gui)
    - platform: The platform to use, e.g., 'qradar', 'elastic' or 'defender

    Returns:
    - str: The name or path of the template file corresponding to the platform.
    """
    if mode == "cli":
        choices = [
            questionary.Choice(
                title=f"{name} - {meta.get('description', 'no description')}",
                value=name
            )
            for name, meta in VALID_PLATFORMS.items()
        ] + [questionary.Choice("Quit", value="quit")]

        platform = questionary.select(
            "Choose a platform to use:",
            choices=choices
        ).ask()

        if platform in ("quit", None):
            sys.exit(1)

        try:
            templates = load_templates(platform)
            return platform, templates
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

    else:
        platform = platform or "qradar"
        return platform, None

def choose_mode() -> str:

    """
    Choose between gui and CLI mode.

    str: Return the choosen mode.
    """
    mode = questionary.select(
        "Choose interface mode:",
        choices=[
            questionary.Choice("CLI (terminal)", value="cli"),
            questionary.Choice("GUI (graphical)", value="gui"),
            questionary.Choice("Quit", value="quit")
        ]
    ).ask() or "quit"

    if mode == "quit":
        sys.exit(1)
    return mode

def normalize_lookback(lookback: str, platform) -> str:

    """
    Normalises lookback values for Defender/Elastic platform.
    
    Args:
    - lookback (str): The string value to transform to correct format.

    Returns:
    - str: A lookback value in the correct format for query iteration.
    """
    lookback = lookback.strip().lower()
    match = re.match(r"(\d+)\s*(minutes?|hours?|days?)", lookback)

    if not match:
        return None
    
    value, unit = match.groups()
    value = int(value)

    if value <=0: 
        return None

    is_defender_or_elastic = platform in ("defender", "elastic")

    match unit:
        case "minute" | "minutes":
            return f"{value}m" if is_defender_or_elastic else f"{value} MINUTES"
        case "hour" | "hours":
            return f"{value}h" if is_defender_or_elastic else f"{value} HOURS"
        case "day":
            return f"{value*24}h" if is_defender_or_elastic else f"{value} DAYS"
        case _:
            return None

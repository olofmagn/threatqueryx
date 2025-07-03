import questionary
import sys

from typing import List

from utils.utils import validate
from utils.utils import normalize_lookback
from utils.utils import choose_mode
from utils.query_builder import build_query

"""
Provide an cli interface to specify the template and platform for search
"""

class QueryCli:
    def __init__(self, platform: str, templates: List[str]) -> str:
        self.platform = platform
        self.templates = templates
        self.include_post_pipeline = False

    def build_query_for_cli(self) -> None:
            """
            Build query for cli
            """
            if not self.templates:
                print("No templates available.")
                sys.exit(1)

            choices = [
                    questionary.Choice(
                        title=f"{name} - {meta.get('description', 'No description')}",
                        value = name
                        )
                    for name, meta in self.templates.items()
                    ] + [questionary.Choice("Quit", value="quit")]

            template_name = questionary.select(
                    "Choose a template to use:",
                    choices=choices).ask()

            if template_name in ("quit", None):
                sys.exit(1)

            template = self.templates[template_name]
            print(f"\n{template.get('description', 'no help')}\n")

            inputs = {}
            for key, meta in template.get("optional_fields", {}).items():
                while True:
                    value = input(f"{key} ({meta.get('help', '')}): ").strip()
                    if value == "": # User skipped optional field
                        break
                    if not value:
                        continue
                    if "validation" in meta:
                        valid, msg = validate(value, meta["validation"])
                        if not valid:
                            print(f"Invalid input for {key}: {msg}")
                            continue

                    inputs[key] = value
                    break # Exit if we get a valid result
            
            # Post-pipeline summarisation
            if self.platform == "defender":
                self.include_post_pipeline = input(
                        "Include summarization (post_pipeline)? [y/N]: ").strip().lower() == "y"

            while True:
                lookback = input("Time range (default '10 MINUTES'): ").strip()
                if not lookback:
                    lookback = "10 minutes"

                duration = normalize_lookback(lookback, self.platform)

                if duration is None:
                    print("Invalid input")
                    continue
                break

            query = build_query(template, inputs, duration, self.platform, self.include_post_pipeline)
            print("\nGenerated Query:\n")
            print(query)


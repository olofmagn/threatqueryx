
"""
Cli interface
"""

import questionary
import sys

from typing import Dict, Tuple
from questionary import Separator

from utils.configuration import validate
from utils.configuration import normalize_lookback
from utils.configuration import resolve_platform_and_templates
from utils.configuration import load_templates

from utils.query_builder import build_query


class QueryCli:
    def __init__(self, platform: str, templates: Dict[str, any]) -> None:
        self.platform = platform
        self.templates = templates
        self.include_post_pipeline = False

    def build_query_for_cli(self) -> None:
        
        """
        Build query for cli given template, inputs, duration, platform and post_pipeline.
        """
        if not self.templates:
            print("No templates available.")
            sys.exit(1)

        template_name, template = self.get_template()

        inputs = self.get_inputs(template)
        duration = self.get_lookback()

        query = build_query(template, inputs, duration, self.platform, self.include_post_pipeline)
        print("Generated query:\n")
        print(query)

    def get_template(self) -> Tuple [str, dict]:

        """
        Collects the name of the template selected by the user.
        Allows going back to platform selection and reloading templates.

        """
        while True:
            choices = [
                questionary.Choice(
                    title=f"{name} - {meta.get('description', 'No description')}",
                    value=name
                )

                for name, meta in self.templates.items()
            ] + [
                Separator("---"),
                questionary.Choice("Go back to platform selection", value="back"),
                questionary.Choice("Quit", value="quit")
            ]

            template_name = questionary.select(
                "Choose a template to use:",
                choices=choices
            ).ask()

            if template_name in ("quit", None):
                sys.exit(1)

            if template_name == "back":
                self.platform, self.templates = resolve_platform_and_templates(mode="cli", platform=None)
                continue  # Restart template selection loop

            template = self.templates[template_name]

            return template_name, template

    def get_inputs(self, template) -> Dict[str,any]:
        """
        Collect optional input parameters from the user, with validation if defined.
        Also asks for post-pipeline summarization if platform is Defender.

        Arguments:
        - template (str): template of the given platform.

        Returns:
        - Dict[str, any]: A dictionary of inputs.
        """

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
                break  

        # Post-pipeline summarisation
        if self.platform == "defender":
            while True:
                choice = input("Include summarisation (post_pipeline)? [y/n]: ").strip().lower()

                if choice in ("y", "n"):
                    self.include_post_pipeline = (choice == "y")
                    break
                print("Please enter 'y' or 'n'.")

        return inputs 

    def get_lookback(self) -> str:
        """
        Collect lookback data from the user for the search query.

        Returns:
        - str: A duration string of a lookback value.
        """

        while True:
            lookback = input("Time range (default '10 MINUTES'): ").strip()

            if not lookback:
                lookback = "10 minutes"

            duration = normalize_lookback(lookback, self.platform)

            if duration is None:
                print("Invalid input")
                continue
            break

        return duration

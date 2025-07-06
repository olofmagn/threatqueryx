import questionary
import sys

from typing import Dict

from utils.utils import validate
from utils.utils import normalize_lookback
from utils.query_builder import build_query

"""
Provide an cli interface to specify the template and platform for search.
"""

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

        template_name = self.get_template()
        template = self.templates[template_name]
        print(f"\n{template.get('description', 'no help')}\n")

        inputs = self.get_inputs(template)
        duration = self.get_lookback()

        query = build_query(template, inputs, duration, self.platform, self.include_post_pipeline)
        print("Generated query:\n")
        print(query)

    def get_template(self) -> str:

        """
        Collects the name of the template selected by the user.
        """
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

        return template_name

    def get_inputs(self, template) -> Dict[str,any]:
        """
        Collect optional input parameters from the user, with validation if defined.
        Also asks for post-pipeline summarization if platform is Defender.

        Arguments:
        - template (str): template of the given platform
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
        Collect lookback data from the user for the search query
        """

        while True:
            lookback = input("Time range (default '10 MINUTES'): ").strip()
            if not lookback:
                lookback = "10 minutes"

            duration = normalize_lookback(lookback, self.platform)
            print(duration)

            if duration is None:
                print("Invalid input")
                continue
            break

        return duration

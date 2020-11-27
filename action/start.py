"""
Starts and Registers a GitHub Actions Self Hosted Runner using an ECS Task Definition.
"""

import os

from rich.console import Console

if __name__ == "__main__":
    console = Console()
    console.print([var for var in os.environ if var.startswith("INPUT_")])

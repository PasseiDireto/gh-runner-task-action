"""
Starts and Registers a GitHub Actions Self Hosted Runner using an ECS Task Definition.
"""

import json
import os

import boto3
from rich.console import Console

if __name__ == "__main__":
    console = Console()
    input_data = [var for var in os.environ if var.startswith("INPUT_")]
    general_data = [var for var in os.environ if not var.startswith("INPUT_")]
    console.print("general data: ", general_data)
    console.print("input data: ", input_data)
    task_params_file = os.environ.get("INPUT_TASK_PARAMS_FILE")
    base_config = {}
    if task_params_file and os.path.exists(task_params_file):
        base_config = json.loads(open(task_params_file).read())
    console.print(base_config)
    client = ecr_client = boto3.client("ecr")

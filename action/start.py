"""
Starts and Registers a GitHub Actions Self Hosted Runner using an ECS Task Definition.
"""

import json
import os

import boto3
from rich.console import Console


def get_input(environ):
    prefix = "INPUT_"
    return {
        snake_to_camel(k.removeprefix(prefix)): v
        for k, v in environ.items()
        if k.startswith(prefix)
    }


def snake_to_camel(name):
    u_camel_case = "".join(word.title() for word in name.lower().split("_"))
    return u_camel_case[0].lower() + u_camel_case[1:]


if __name__ == "__main__":
    console = Console()
    input_data = get_input(os.environ)
    general_data = {v: os.environ[v] for v in os.environ if not v.startswith("INPUT_")}
    task_params_file = os.environ.get("INPUT_TASK_PARAMS_FILE")
    base_config = json.loads(open("./task-params-template.json").read())
    if task_params_file and os.path.exists(task_params_file):
        base_config.update(json.loads(open(task_params_file).read()))
    for key, value in input_data.items():
        if key in base_config:
            base_config[key] = value
    base_config["startedBy"] = general_data.get("GITHUB_ACTOR", "unknown")
    console.print(base_config)
    ecr = boto3.client("ecs")
    ecr.run_task(**base_config)

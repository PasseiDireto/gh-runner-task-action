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
    console.print(input_data)
    console.print(general_data)
    task_params_file = os.environ.get("INPUT_TASK_PARAMS_FILE")
    base_config = json.loads(open("./task-params-template.json").read())
    if task_params_file and os.path.exists(task_params_file):
        base_config.update(json.loads(open(task_params_file).read()))
    for key, value in input_data.items():
        if key in base_config:
            base_config[key] = value
    repo = general_data["GITHUB_REPOSITORY"].split("/")[1]
    base_config["group"] = f"gh-runner:{repo}"
    base_config["startedBy"] = general_data.get("GITHUB_ACTOR", "unknown")
    base_config["overrides"]["containerOverrides"][0]["environment"] = [
        {"name": "GITHUB_PERSONAL_TOKEN", "value": input_data["githubPat"]},
        {"name": "GITHUB_OWNER", "value": general_data["GITHUB_REPOSITORY_OWNER"]},
        {"name": "GITHUB_REPOSITORY", "value": repo},
        {"name": "RUNNER_NAME", "value": general_data["GITHUB_JOB"]},
    ]
    base_config["networkConfiguration"]["awsvpcConfiguration"]["subnets"] = input_data[
        "subnets"
    ].split(",")
    if input_data.get("securityGroups"):
        base_config["networkConfiguration"]["awsvpcConfiguration"][
            "securityGroups"
        ] = input_data.get("securityGroups").split(",")
    console.print(base_config)
    ecr = boto3.client("ecs")
    console.print(base_config)
    response = ecr.run_task(**base_config)
    console.print(response)

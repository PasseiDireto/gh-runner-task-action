"""
ECS Task Definition Config related classes
"""
import json
import os
from typing import Optional


class Config:
    """
    Represents the ECS Task Definition execution config. Basically represents the ECS.run_task() params:
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ecs.html#ECS.Client.describe_tasks
    """

    repository: str = ""
    wait: str = ""

    def __init__(
        self, task_params_file: Optional[str]
    ):  # pylint: disable=unsubscriptable-object
        # https://github.com/PyCQA/pylint/issues/3882
        self._config = json.loads(open("./task-params-template.json").read())
        if task_params_file and os.path.exists(task_params_file):
            self._config.update(json.loads(open(task_params_file).read()))

    def set(self, **kwargs):
        for key, value in kwargs.items():
            if key in self._config:
                self._config[key] = value

    def set_repo(self, env_repo: str):
        self.repository = env_repo.split("/")[1]

    def set_container_env(self, env_vars: dict):
        list_vars = []
        for name, value in env_vars.items():
            list_vars.append({"name": name, "value": value})
        self._config["overrides"]["containerOverrides"][0]["environment"] = list_vars

    def set_subnets(self, subnets: str):
        if subnets:
            self._config["networkConfiguration"]["awsvpcConfiguration"][
                "subnets"
            ] = subnets.split(",")

    def set_security_groups(self, security_groups: str):
        if security_groups:
            self._config["networkConfiguration"]["awsvpcConfiguration"][
                "securityGroups"
            ] = security_groups.split(",")

    def as_dict(self):
        return self._config

    @property
    def cluster(self):
        return self._config.get("cluster")

    def __str__(self):
        return repr(self._config)

"""
ECS Task Execution related classes
"""
import json
import logging
import time
from pathlib import Path
from typing import Optional

import boto3


class TaskConfig:
    """
    Represents the ECS Task Definition execution config. Basically represents the ECS.run_task() params:
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ecs.html#ECS.Client.run_task
    """

    repository: str = ""
    wait: str = ""
    logger = logging.getLogger("TaskConfig")

    def __init__(
        self, task_params_file: Optional[str] = ""
    ):  # pylint: disable=unsubscriptable-object
        # https://github.com/PyCQA/pylint/issues/3882
        self._config = self._default_template()
        self._config.update(self._custom_template(task_params_file))

    def set(self, **kwargs):
        for key, value in kwargs.items():
            if key in self._config:
                self._config[key] = value

    def set_repository(self, env_repo: str):
        self.repository = env_repo.split("/")[-1]

    def set_container_env(self, env_vars: dict):
        list_vars = []
        for name, value in env_vars.items():
            list_vars.append({"name": name, "value": value})
        self._config["overrides"]["containerOverrides"][0]["environment"] = list_vars

    def set_capacity_provider(self, provider: str):
        self._config["capacityProviderStrategy"][0]["capacityProvider"] = provider

    def as_dict(self):
        return self._config

    @property
    def cluster(self):
        return self._config.get("cluster")

    @property
    def task_definition(self):
        return self._config.get("taskDefinition")

    def __str__(self):
        return repr(self._config)

    def _default_template(self):
        path = (
            Path(__file__)
            .parent.parent.absolute()
            .joinpath("task-params-template.json")
        )
        return json.loads(open(path).read())

    def _custom_template(self, task_params_file):
        path = Path(task_params_file).absolute()
        if path.is_file():
            self.logger.info(f"Using custom task definition from {path}")
            return json.loads(open(task_params_file).read())
        self.logger.info(f"No custom task definition file found at {path}")
        self.logger.info(f"Did you remember checking out your code first?")
        return {}


class Task:
    """
    Represents a task ECS execution, based on a task definition.
    """

    task_arn = None
    retry_delay = 5
    desired_status = "RUNNING"

    def __init__(self, config: TaskConfig):
        self.config = config
        self.client = boto3.client("ecs")
        self.logger = logging.getLogger("Task")

    def run(self):
        self.logger.info("Start task")
        response = self.client.run_task(**self.config.as_dict())
        self.task_arn = response["tasks"][0]["taskArn"]

    def wait(self):
        if not self.task_arn:
            self.logger.error("You can't 'wait' before calling run()")
            return
        self.logger.info(
            f"Waiting for the task to reach '{self.desired_status}' status"
        )

        status = "UNKNOWN"
        while status != self.desired_status:
            info = self.client.describe_tasks(
                cluster=self.config.cluster, tasks=[self.task_arn]
            )
            status = info["tasks"][0]["lastStatus"]
            self.logger.info(f"status still {status}. Waiting for 'RUNNING'")
            time.sleep(self.retry_delay)

    @property
    def url(self):
        base_url = "https://console.aws.amazon.com/ecs/home#/clusters"
        return f"{base_url}/{self.config.cluster}/tasks/{self.task_id}/details"

    @property
    def task_id(self):
        return self.task_arn.split("/")[-1]

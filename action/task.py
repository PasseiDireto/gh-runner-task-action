"""
ECS Task Execution related classes
"""
import json
import logging
import time
from pathlib import Path
from typing import List, Optional

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
        self.logger.info("Did you remember checking out your code first?")
        return {}


class Task:
    """
    Represents multiple task ECS execution, based on a task definition.
    """

    task_arns: List[str] = []
    retry_delay = 2
    desired_status = "RUNNING"
    error_status = "STOPPED"

    def __init__(self, config: TaskConfig):
        self.config = config
        self.client = boto3.client("ecs")
        self.logger = logging.getLogger("Task")

    def run(self):
        self.logger.info("Start task")
        response = self.client.run_task(**self.config.as_dict())
        self.task_arns = [task["taskArn"] for task in response["tasks"]]

    def wait(self):
        """
        Wait for at least one job to be on the desired status. If one task fails before that, the whole procedure will
        abort.
        :raises: RuntimeError when a task placement fails
        """
        if not self.task_arns:
            self.logger.error("You can't 'wait' before calling run()")
            return
        self.logger.info(
            f"Waiting for the at least one task task to reach '{self.desired_status}' status"
        )

        status = self.get_task_status()
        while self.desired_status not in status:
            status = self.get_task_status()
            if self.error_status in status:
                raise RuntimeError(
                    f"Something went wrong starting the task. The status now is: '{status}'"
                )
            self.logger.info(
                f"status are '{','.join(status)}'. Waiting for at least one  '{self.desired_status}'"
            )
            time.sleep(self.retry_delay)

    def get_task_status(self) -> List[str]:
        info = self.client.describe_tasks(
            cluster=self.config.cluster, tasks=self.task_arns
        )
        return [task["lastStatus"] for task in info["tasks"]]

    @property
    def url(self):
        base_url = "https://console.aws.amazon.com/ecs/home#/clusters"
        return f"{base_url}/{self.config.cluster}/tasks/"

    @property
    def task_ids(self) -> List[str]:
        return [task_arn.split("/")[-1] for task_arn in self.task_arns]

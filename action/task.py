"""
ECS Task Execution related classes
"""
import logging
import time

import boto3

from action.config import Config


class Task:
    """
    Represents a task ECS execution, based on a task definition.
    """

    task_arn = None
    retry_delay = 5
    desired_status = "RUNNING"

    def __init__(self, config: Config):
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
        base_url = "https://us-east-2.console.aws.amazon.com/ecs/home#/clusters"
        return f"{base_url}/{self.config.cluster}/tasks/{self.task_id}/details"

    @property
    def task_id(self):
        return self.task_arn.split("/")[-1]

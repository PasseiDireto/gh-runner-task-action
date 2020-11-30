"""
Starts and Registers a GitHub Actions Self Hosted Runner using an ECS Task Definition.
"""

import logging
import os
import sys

from rich.console import Console
from rich.logging import RichHandler
from rich.traceback import install

from action.config import Config
from action.params import Input
from action.task import Task

console = Console()

FORMAT = "%(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=FORMAT,
    datefmt="[%X]",
    handlers=[RichHandler(markup=True, rich_tracebacks=True)],
)
install()
logger = logging.getLogger("main")

if __name__ != "__main__":
    sys.exit(0)

env = os.environ
input = Input(dict(env))  # pylint: disable=redefined-builtin
task_params_file = env.get("INPUT_TASK_PARAMS_FILE")
config = Config(task_params_file)
logger.info(
    f"Start task execution with defition '{config.task_definition}' on cluster '{config.cluster}'"
)
config.set_repository(env["GITHUB_REPOSITORY"])
config.set(
    **input.as_dict(),
    group=f"gh-runner:{config.repository}",
    startedBy=env.get("GITHUB_ACTOR", "UNKNOWN"),
)
config.set_container_env(
    {
        "GITHUB_PERSONAL_TOKEN": input["githubPat"],
        "GITHUB_OWNER": env["GITHUB_REPOSITORY_OWNER"],
        "GITHUB_REPOSITORY": config.repository,
        "RUNNER_NAME": env["GITHUB_JOB"],
    }
)
config.set_subnets(input.get("subnets"))
config.set_security_groups(input.get("securityGroups"))
logger.info("Ready to execute with config:")
logger.info(config.as_dict())

task = Task(config)
task.run()
if input.should_wait:
    task.wait()
    logger.info(f"Runner ready to receive jobs: {task.task_arn}")

logger.info("Task successfuly created.")
logger.info(f"You can follow it on: {task.url}")

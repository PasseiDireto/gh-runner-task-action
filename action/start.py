"""
Starts and Registers a GitHub Actions Self Hosted Runner using an ECS Task Definition.
"""

import logging
import os

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


if __name__ == "__main__":
    env = os.environ
    input = Input(dict(env))  # pylint: disable=redefined-builtin
    task_params_file = env.get("INPUT_TASK_PARAMS_FILE")
    config = Config(task_params_file)
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
    task = Task(config)
    task.run()
    if input.should_wait:
        task.wait()

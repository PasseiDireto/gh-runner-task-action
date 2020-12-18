import json
import os

import boto3
import mock
import pytest
from moto import mock_ec2, mock_ecs
from moto.ec2 import utils as ec2_utils

from action.task import Task, TaskConfig


@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


def ecs_init():
    client = boto3.client("ecs")
    ec2 = boto3.resource("ec2")
    client.create_cluster(clusterName="abc")
    test_instance = ec2.create_instances(MinCount=1, MaxCount=1)[0]
    instance_id_document = json.dumps(
        ec2_utils.generate_instance_identity_document(test_instance)
    )

    client.register_container_instance(
        cluster="abc", instanceIdentityDocument=instance_id_document
    )
    client.register_task_definition(
        family="xyz",
        containerDefinitions=[],
    )


@mock_ec2
@mock_ecs
def test_task_run(aws_credentials):
    # https://github.com/spulec/moto/blob/master/tests/test_ecs/test_ecs_boto3.py#L1088
    ecs_init()
    config = TaskConfig()
    config.set(cluster="abc", taskDefinition="xyz")
    Task.retry_delay = 0
    task = Task(config)
    task.run()
    task.wait()
    assert task.task_arn
    assert task.task_id
    assert task.task_id in task.url


@mock_ec2
@mock_ecs
@mock.patch("action.task.Task.run")
@mock.patch("action.task.Task.get_task_status")
def test_task_wait_failure(get_task_status, run, aws_credentials):
    get_task_status.return_value = "STOPPED"
    config = TaskConfig()
    Task.retry_delay = 0
    task = Task(config)
    task.task_arn = "abc123"
    task.run()
    with pytest.raises(RuntimeError):
        task.wait()

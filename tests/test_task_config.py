import os
import pathlib

from action.task import TaskConfig


def test_init_ok():
    config = TaskConfig()
    assert config.cluster is None
    assert config.task_definition is None


def test_set_ok():
    config = TaskConfig()
    config.set(group="TEST", unknownParam=123)
    assert config.as_dict()["group"] == "TEST"
    assert "unknownParam" not in config.as_dict()


def test_set_repo():
    config = TaskConfig()
    config.set_repository("Organization/my-repo")
    assert config.repository == "my-repo"


def test_env_var():
    expected = {"name": "ENV_CONFIG", "value": "ABC"}
    config = TaskConfig()
    config.set_container_env(env_vars={"ENV_CONFIG": "ABC"})
    assert (
        config.as_dict()["overrides"]["containerOverrides"][0]["environment"][0]
        == expected
    )


def test_custom_task_params(tmpdir):
    p = pathlib.Path(os.getcwd()).joinpath("task-params.json")
    p.touch()
    p.write_text('{"cluster": "123a"}')
    config = TaskConfig(task_params_file="task-params.json")
    assert config.cluster == "123a"
    p.unlink()


def test_capacity_provider():
    config = TaskConfig()
    config.set_capacity_provider("abc")
    assert config.as_dict()["capacityProviderStrategy"][0]["capacityProvider"] == "abc"


def test_empty_capacity_provider():
    config = TaskConfig()
    config.set_capacity_provider(None)
    assert "capacityProviderStrategy" not in config.as_dict()

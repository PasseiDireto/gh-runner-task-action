from action.task import TaskConfig


def test_init_ok():
    config = TaskConfig()
    assert config.cluster is None
    assert config.task_definition is None


def test_set_ok():
    config = TaskConfig()
    config.set(launchType="TEST", unknownParam=123)
    assert len(config.as_dict()["capacityProviderStrategy"][0]) == 3
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


def test_capacity_provider():
    config = TaskConfig()
    config.set_capacity_provider("abc")
    assert config.as_dict()["capacityProviderStrategy"][0]["capacityProvider"] == "abc"

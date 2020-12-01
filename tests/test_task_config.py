from action.task import TaskConfig


def test_init_ok():
    config = TaskConfig()
    assert config.cluster is None
    assert config.task_definition is None


def test_set_ok():
    config = TaskConfig()
    config.set(launchType="TEST", unknownParam=123)
    assert config.as_dict()["launchType"] == "TEST"
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


def test_subnets():
    expected = ["sub1", "sub2"]
    config = TaskConfig()
    config.set_subnets("sub1,sub2")
    assert (
        config.as_dict()["networkConfiguration"]["awsvpcConfiguration"]["subnets"]
        == expected
    )


def test_security_groups():
    expected = ["sg1", "sg2"]
    config = TaskConfig()
    config.set_security_groups("sg1,sg2")
    assert (
        config.as_dict()["networkConfiguration"]["awsvpcConfiguration"][
            "securityGroups"
        ]
        == expected
    )

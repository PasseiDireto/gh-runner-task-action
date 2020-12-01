from action.params import Input


def test_input_from_env():
    input_dict = {
        "INPUT_ABC": 123,
        "INPUT_CAMEL_CASE": "XYZ",
        "OTHER_INPUT": "NOTHERE",
    }
    input = Input(input_dict)
    assert "OTHER_INPUT" not in input
    assert input["abc"] == 123
    assert input["camelCase"] == "XYZ"
    assert input.as_dict()["camelCase"] == "XYZ"


def test_should_wait():
    input = Input({"INPUT_WAIT": "true"})
    assert input.should_wait


def test_dict_capabilities():
    input = Input({"INPUT_TEST": 123, "INPUT_TEST2": "XYZ"})
    assert input.get("test") == 123
    assert not input.get("doesnotexist", False)
    assert input.items()


def test_set_item():
    input = Input({})
    input["test"] = 123
    assert input["test"] == 123

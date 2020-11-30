"""
Input related classes
"""
from typing import Any, Dict


class Input:
    """
    Represents an input from GHA executor, containing the needed params to properly execute the action
    """

    prefix = "INPUT_"

    def __init__(self, inputs: Dict[str, Any]):
        self._inputs = {
            self.snake_to_camel(k.removeprefix(self.prefix)): v
            for k, v in inputs.items()
            if k.startswith(self.prefix)
        }

    @classmethod
    def snake_to_camel(cls, name):
        u_camel_case = "".join(word.title() for word in name.lower().split("_"))
        return u_camel_case[0].lower() + u_camel_case[1:]

    def get(self, *args):
        return self._inputs.get(*args)

    def as_dict(self):
        return self._inputs

    def __setitem__(self, key, item):
        self._inputs[key] = item

    def __getitem__(self, key):
        return self._inputs[key]

    def __repr__(self):
        return repr(self._inputs)

    def __len__(self):
        return len(self._inputs)

    def items(self):
        return self._inputs.items()

    def __iter__(self):
        return iter(self.__dict__)

    @property
    def should_wait(self):
        return self._inputs["wait"] == "true"

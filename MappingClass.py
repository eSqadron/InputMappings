import json
from typing import Callable, Optional, Dict


def basicActionFunction(name):
    raise ValueError(f"No function mapped to action {name}")


class Mapping:
    def __init__(self, name, function=None):
        self.name = name

        self.kwargs = {}
        self.args = []

        if function is None:
            self._function = basicActionFunction(name)
        else:
            self._function = function

    @property
    def function(self):
        return self._function

    @function.setter
    def function(self, function):
        if isinstance(function, Callable):
            self._function = function
        else:
            raise ValueError("function must be a callable")

    def executeAction(self, *args, **kwargs):
        self._function(*self.args, *args, **self.kwargs, **kwargs)


class MappingClass:
    """
    Class that holds action and axis mapping
    Action/Axis name is mapped to relevant function
    """

    def __init__(self):
        self.standard_mappings: Dict[str, Mapping] = {}

    def map_standard_action(self, name, function):
        """
        Map action name to relevant function
        :param name: name of an action. Function will be later referenced by this name (string)
        :param function: function that is called when action is executed (callable)
        :return: None
        """
        self.standard_mappings[name] = Mapping(name, function)

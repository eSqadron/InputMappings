import json
from typing import Callable, Optional, Dict


def basicActionFunction(name):
    raise ValueError(f"No function mapped to action {name}")


class Mapping:
    def __init__(self, name, function=None):
        self.name = name
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

    def executeAction(self, *argv):
        self._function(*argv)


class MappingClass:
    """
    Class that holds action and axis mapping
    Action/Axis name is mapped to relevant function
    """

    def __init__(self):
        self.standard_mappings = {}

    def map_standard_action(self, name, function):
        """
        Map action name to relevant function
        :param name: name of an action. Function will be later referenced by this name (string)
        :param function: function that is called when action is executed (callable)
        :return: None
        """
        self.standard_mappings[name] = Mapping(name, function)

    def load_from_json(self, file_path: str, names_ref: Optional[Dict] = None) -> None:
        """
        Load all mappings from json file
        file structure:
        {
          "standard action mappings":
          {
            "action name": "related function",
            "action name2": "related function2"
          }
        }
        :param file_path: path to file to be loaded
        :param names_ref: name references, for example {"self":self}, if all functions are defined
        in the same class as this function is called from. Or {"Cls1":cls1_instance, "Cls2":cls2_instance}
        if functions are spread among various instances of various classes.
        """
        f = open(file_path)
        data = json.load(f)
        for i, j in data['standard action mappings'].items():
            if names_ref is not None:
                self.map_standard_action(i, eval(j, names_ref))
            else:
                self.map_standard_action(i, eval(j))

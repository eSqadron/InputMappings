from typing import Callable


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
        self.actionMappings = {}
        self.axisMappings = {}

    def mapAction(self, name, function):
        """
        Map Action, name to relevant function
        :param name: name of an action (string)
        :param function: function that is called when action is executed (callable)
        :return: None
        """
        self.actionMappings[name] = Mapping(name, function)

    def mapAxis(self, name, function):
        """
        Map Axis, name to relevant function
        :param name: name of an axis (string)
        :param function: function that is called when axion is executed (callable with preferably two parameters, first
        angle, second movement strength/speed. Should work with different amount and type of params, but Input classes are
        written for this kind of setup)
        :return: None
        """
        self.axisMappings[name] = Mapping(name, function)

    # def executeAction(self, name, *argv):
    #     """
    #     executes action with given name
    #     :param name: name of action to execute
    #     :param argv: params to pass to action (preferably angle and speed)
    #     :return:
    #     """
    #     self.actionMappings[name].executeAction(*argv)

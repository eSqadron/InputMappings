from abc import ABC
from typing import Tuple, Optional, Callable, Type, Dict, Union

from evdev import InputDevice, categorize, ecodes, KeyEvent, SynEvent, AbsEvent, list_devices, InputEvent
import threading
import time

from MappingClass import MappingClass, Mapping

from numpy import rad2deg
from math import atan2, sqrt


class DeviceError(FileNotFoundError):
    def __init__(self, message='Problem with Device!'):
        super().__init__(message)


class NonExistingPathError(DeviceError):
    def __init__(self, message='Can\'t find any device under given path'):
        super().__init__(message)


class WrongDeviceError(DeviceError):
    def __init__(self, message='There is differently named device under given event!'):
        super().__init__(message)


class DeviceNotPlugged(DeviceError):
    def __init__(self, message='Device can\'t be found under any path!'):
        super().__init__(message)


class NonExistingInput(DeviceError):
    def __init__(self, message='Button/joystick/etc. under given name doesn\'t exist in this device!'):
        super().__init__(message)


class ActionError(DeviceError):
    def __init__(self, message='Nothing mapped to this key!'):
        super().__init__(message)


class PlaceholderException(Exception):
    def __init__(self, message='Something went terribly wrong if you are seeing this message!'):
        super().__init__(message)


class EvdevInput:
    pass


class Button(EvdevInput):
    def __init__(self, ev_name, frontend_name, mapping_to_execute_on_press: Optional[Mapping] = None,
                 mapping_to_execute_on_release: Optional[Mapping] = None,
                 mapping_to_while_pressed: Optional[Mapping] = None):
        self.ev_name = ev_name
        self.frontend_name = frontend_name
        self.mapping_to_execute_on_press = mapping_to_execute_on_press
        self.mapping_to_while_pressed = mapping_to_while_pressed
        self.mapping_to_execute_on_release = mapping_to_execute_on_release

        self.is_pressed = False

    def update_single_button(self, ev_name, ev_val):
        found = False
        if isinstance(ev_name, list):
            if self.ev_name in ev_name:
                found = True
        elif isinstance(ev_name, str):
            if ev_name == self.ev_name:
                found = True

        if found:
            if ev_val == 1:
                self.is_pressed = True
            elif ev_val == 0:
                self.is_pressed = False

            return self

        else:
            return None

    def execute_action(self):
        something_executed = False
        if self.mapping_to_execute_on_press is not None:
            self.mapping_to_execute_on_press.executeAction()
            something_executed = True

        while self.is_pressed:
            if self.mapping_to_while_pressed is not None:
                self.mapping_to_while_pressed.executeAction()
                something_executed = True

        if self.mapping_to_execute_on_release is not None:
            self.mapping_to_execute_on_release.executeAction()
            something_executed = True

        if not something_executed:
            raise ActionError()


class Joystick(EvdevInput):
    def __init__(self, x_name, y_name, joystick_front_name, mapping_to_execute: Optional[Mapping] = None,
                 thresholds=0.3, normalizer_div=1, normalizer_sub=0):
        self.joystick_name = joystick_front_name
        self.name_xy = [x_name, y_name]
        self.last_pos_xy = [0, 0]
        self.mapping_to_execute = mapping_to_execute

        self.thresholds = thresholds
        self.normalizer_div = normalizer_div
        self.normalizer_sub = normalizer_sub

        self.execute_action = None

    def update_single_joystick(self, ev_name, ev_val):
        found = False

        for i in range(2):
            if self.name_xy[i] == ev_name:
                # Turn pad range (ex. 0-256) into -1-1 range
                self.last_pos_xy[i] = (ev_val - self.normalizer_sub) / self.normalizer_div
                found = True

        if found:
            return self
        else:
            return None

    def execute_action_ang_str(self):
        if self.mapping_to_execute is None:
            raise ActionError()

        while abs(self.last_pos_xy[0]) > self.thresholds or abs(self.last_pos_xy[1]) > self.thresholds:
            # TODO - Zrobić whilea tak jakby tablicowo

            x_j, y_j = self.last_pos_xy[0], -self.last_pos_xy[1]
            # print(x_j, y_j, spec_arctan(x_j, y_j), sqrt(x_j ** 2 + y_j ** 2))
            # TODO - wywalić tego mina
            self.mapping_to_execute.executeAction(rad2deg(atan2(x_j, y_j)), min(sqrt(x_j ** 2 + y_j ** 2), 1))

    def execute_action_x_y(self):
        if self.mapping_to_execute is None:
            raise ActionError()

        while abs(self.last_pos_xy[0]) > self.thresholds or abs(self.last_pos_xy[1]) > self.thresholds:
            # TODO - Zrobić whilea tak jakby tablicowo
            x_j, y_j = self.last_pos_xy[0], -self.last_pos_xy[1]
            self.mapping_to_execute.executeAction(x_j, y_j)


class EvdevDevice(ABC):
    def __init__(self):
        self.name: Optional[str] = None
        self.device: Optional[InputDevice] = None

        self.instance_check_dict: Dict[InputEvent, Callable[[InputEvent], Optional[EvdevInput]]] = \
            {AbsEvent: self.update_joysticks_states, KeyEvent: self.update_keys_states}

        self.joysticks_list = []

        self.buttons_list = []

        self.capabilities = []

        self.mappingObject = None

        self.connected = False

    def connect(self, wait_time=1, repeats=5):
        for path in list_devices():
            print(InputDevice(path).name)
            if InputDevice(path).name == self.name:
                self.connected = True
                print("connected")
                self.device = InputDevice(path)
                break
        else:
            raise DeviceNotPlugged()

    def update_joysticks_states(self, input_event):
        input_event_str = str(input_event)
        pos = input_event_str.find("ABS")
        if pos == -1:
            raise IndexError("NO ABS in ABS")
        ev_name = str(input_event)[pos:-1]
        ev_val = input_event.event.value
        for i in self.joysticks_list:
            moved_joystick = i.update_single_joystick(ev_name, ev_val)
            if moved_joystick is not None:
                return moved_joystick

    def update_keys_states(self, input_event):
        ev_name = input_event.keycode
        ev_state = input_event.keystate
        for i in self.buttons_list:
            clicked_button = i.update_single_button(ev_name, ev_state)
            if clicked_button is not None:
                return clicked_button

    def update_states(self, input_event):
        for input_type, proper_update_function in self.instance_check_dict.items():
            if isinstance(input_event, input_type):
                if input_type in self.capabilities:
                    return proper_update_function(input_event)

        return None

    def map_key(self, keyInput, actionName, keyState=1):
        if actionName in self.mappingObject.standard_mappings.keys():
            for i in self.buttons_list:
                # print(i.frontend_name)
                if i.frontend_name == keyInput:
                    # print("   the one")
                    if keyState == 1:
                        i.mapping_to_execute_on_press = self.mappingObject.standard_mappings[actionName]
                        # print("event", actionName, "maped")
                    elif keyState == 2:
                        i.mapping_to_while_pressed = self.mappingObject.standard_mappings[actionName]
                    elif keyState == 0:
                        i.mapping_to_execute_on_release = self.mappingObject.standard_mappings[actionName]
                    break
            else:
                raise NonExistingInput()
        else:
            raise IndexError(f"First map the action named {actionName}!")

    def map_joystick(self, joystick_input: str, axisName: str, action_type: str):
        """
        :param action_type: "ang_str" or "x_y", depending whether you want
                            arguments to be passed as angle and strength or x and y
        :param joystick_input: name of joystick on pad TODO - functions showing names and pads and functions allowing addition of other pads
        :param axisName: name of axis in mapping object
        :return: None
        """
        if axisName in self.mappingObject.standard_mappings.keys():
            for i in self.joysticks_list:
                if i.joystick_name == joystick_input:
                    i.mapping_to_execute = self.mappingObject.standard_mappings[axisName]
                    if action_type == "x_y":
                        i.execute_action = i.execute_action_x_y
                    elif action_type == "ang_str":
                        i.execute_action = i.execute_action_ang_str
                    else:
                        raise ValueError("This type of params do not exist!")
                    break
            else:
                raise NonExistingInput()
        else:
            raise IndexError(f"First map the axis named {axisName}!")

    def listen_loop(self, stop_name, stop_state, target):

        for event in self.device.read_loop():
            categorised_event = categorize(event)

            # ABS events are are "floating" events - triggers, joysticks etc.
            if isinstance(categorised_event, AbsEvent):
                # self.to_exec, self.args_for_exec = self.pad.update_states(categorised_event)
                target.executing_joystick = self.update_states(categorised_event)

            # key events are regular button events
            elif isinstance(categorised_event, KeyEvent):
                target.executing_button = self.update_states(categorised_event)

                if categorised_event.keycode == stop_name and categorised_event.keystate == stop_state:
                    break


class X5Pad(EvdevDevice):
    def __init__(self, mappingObject):
        super(X5Pad, self).__init__()

        self.name = "mingpin-X5Pro"

        self.lef_j = Joystick("ABS_X", "ABS_Y", "LEFT_J", normalizer_div=128, normalizer_sub=128)
        self.right_j = Joystick("ABS_RZ", "ABS_Z", "RIGHT_J", normalizer_div=128, normalizer_sub=128)

        self.b_triggers = Joystick("ABS_GAS", "ABS_BRAKE", "TRIGGERS", normalizer_div=255, normalizer_sub=0)

        self.cross_buttons = Joystick("ABS_HAT0X", "ABS_HAT0Y", "HAPPY_BUTTONS_J", normalizer_div=1, normalizer_sub=0)
        # To gówno działa jakoś dziwnie, trzeba dziada ogarnąć

        self.y_button = Button("BTN_Y", "BTN_Y")
        self.x_button = Button("BTN_X", "BTN_X")
        self.a_button = Button("BTN_A", "BTN_A")
        self.b_button = Button("BTN_B", "BTN_B")

        self.select_button = Button("BTN_SELECT", "BTN_SELECT")
        self.start_button = Button("BTN_START", "BTN_START")

        self.left_button = Button("BTN_TL", "BTN_LB")
        self.right_button = Button("BTN_TR", "BTN_RB")

        self.left_j_button = Button("BTN_THUMBL", "BTN_LJ")
        self.right_j_button = Button("BTN_THUMBR", "BTN_RJ")

        self.joysticks_list = [self.lef_j, self.right_j, self.b_triggers, self.cross_buttons]

        self.buttons_list = [self.y_button, self.x_button, self.a_button, self.b_button, self.select_button,
                             self.start_button, self.left_button, self.right_button, self.left_j_button,
                             self.right_j_button]

        # print()
        # for i in self.buttons_list:
        #    print(i.frontend_name)
        # print()

        self.capabilities = [AbsEvent, KeyEvent]

        self.device: Optional[InputDevice] = None

        self.mappingObject = mappingObject


class x360Pad(EvdevDevice):
    def __init__(self, mappingObject):
        super(x360Pad, self).__init__()

        self.name = "Xbox 360 Wireless Receiver"

        self.lef_j = Joystick("ABS_X", "ABS_Y", "LEFT_J", normalizer_div=32768, normalizer_sub=0)
        self.right_j = Joystick("ABS_RX", "ABS_RY", "RIGHT_J", normalizer_div=32768, normalizer_sub=0)

        self.b_triggers = Joystick("ABS_Z", "ABS_RZ", "TRIGGERS", normalizer_div=255, normalizer_sub=0)

        self.cross_buttons_j = Joystick("ABS_HAT0X", "ABS_HAT0Y", "CROSS_BUTTONS", normalizer_div=1, normalizer_sub=0)
        # To gówno działa jakoś dziwnie, trzeba dziada ogarnąć

        self.y_button = Button("BTN_Y", "BTN_Y")
        self.x_button = Button("BTN_X", "BTN_X")
        self.a_button = Button("BTN_A", "BTN_A")
        self.b_button = Button("BTN_B", "BTN_B")

        self.select_button = Button("BTN_SELECT", "BTN_SELECT")
        self.start_button = Button("BTN_START", "BTN_START")

        self.left_button = Button("BTN_TL", "BTN_LB")
        self.right_button = Button("BTN_TR", "BTN_RB")

        self.left_j_button = Button("BTN_THUMBL", "BTN_LJ")
        self.right_j_button = Button("BTN_THUMBR", "BTN_RJ")

        self.cross_buttons_b1 = Button("BTN_TRIGGER_HAPPY1", "BTN_L_HAPPY")
        self.cross_buttons_b2 = Button("BTN_TRIGGER_HAPPY2", "BTN_R_HAPPY")
        self.cross_buttons_b3 = Button("BTN_TRIGGER_HAPPY3", "BTN_UP_HAPPY")
        self.cross_buttons_b4 = Button("BTN_TRIGGER_HAPPY4", "BTN_DOWN_HAPPY")

        self.mode_button = Button("BTN_MODE", "BTN_MODE")

        self.joysticks_list = [self.lef_j, self.right_j, self.b_triggers, self.cross_buttons_j]

        self.buttons_list = [self.y_button, self.x_button, self.a_button, self.b_button, self.select_button,
                             self.start_button, self.left_button, self.right_button, self.left_j_button,
                             self.right_j_button, self.mode_button,
                             self.cross_buttons_b1, self.cross_buttons_b2, self.cross_buttons_b3, self.cross_buttons_b4]

        # TODO - add vibrations

        self.capabilities = [AbsEvent, KeyEvent]

        self.device: Optional[InputDevice] = None

        self.mappingObject = mappingObject


class EvdevDeviceInput:
    def __init__(self):
        self.keyActionBindings = {}

        self.to_exec: Optional[MappingClass] = None
        self.executing_joystick: Optional[Joystick] = None
        self.executing_button: Optional[Button] = None

        self.stopKeyName = "BTN_SELECT"  # TODO ogarnąć żeby to modyfikowalne było

        # priority -> device
        self.devices: Dict[int, Type[EvdevDevice]] = {}

        self.on_ActionError: Optional[Callable] = None

        self.additional_exception = PlaceholderException

    def add_device(self, device: EvdevDevice, priority: int, overwrite=False):
        """
        Add new device for it's input to be listened to
        :param device: Instance of a child of EvdevDevice, device to be added
        :param priority: connection priority; lower number - it will be the first for program to try to connect
        :param overwrite: If device under given priority exist - overrite it
        :return: None
        """
        if priority in self.devices and not overwrite:
            raise IndexError("might be overriten!")

        self.devices[priority] = device

    def connect_devices(self):
        """
        Try to connect to all added devices, in ascending priority
        :return: None
        """
        connected = False
        for p, d in sorted(self.devices.items()):
            for i in range(10):
                try:
                    d.connect()
                except DeviceNotPlugged:
                    time.sleep(1)
                    continue
                else:
                    print("device found")
                    connected = True
                    break
            else:
                print("couldn't find device!")

        if not connected:
            raise DeviceNotPlugged()

    def get_primary_device(self, only_connected=True):
        if not only_connected:
            return sorted(self.devices.items())[0][1]

        for p, d in sorted(self.devices.items()):
            if d.connected:
                return d

        return None  # TODO - change to raise

    def listen_and_execute_one_dev(self, device=None):
        if device is None:
            device = self.get_primary_device()
        padInputThread = threading.Thread(target=device.listen_loop, args=(self.stopKeyName, 0, self))
        padInputThread.start()

        while padInputThread.is_alive():
            for executing_input in [self.executing_joystick, self.executing_button]:
                if executing_input is not None:
                    try:
                        executing_input.execute_action()
                    except ActionError as ae:
                        if self.on_ActionError is None:
                            pass
                        else:
                            self.on_ActionError(ae)
                    except self.additional_exception:
                        pass

            self.executing_joystick = None
            self.executing_button = None

    def listen_and_execute_all(self):
        pass
        # TODO - ogarnąć to

    def set_ActionError_feedback(self, rapport_function: Callable[[Exception], None]):
        """
        Set function that will rapport when button that is not mapped was pressed
        :param rapport_function: function that gives user feedback about error (for example log or print of sorts)
        """
        self.on_ActionError = rapport_function

    def set_additional_exception(self, exception: Type[Exception]):
        """
        During mapped function execution some additional exceptions might occur. If they derive from one class, you may
        set up this parameter to catch them inside this loop.
        :param exception: derivative of Exception, to be caught in the loop
        """
        self.additional_exception = exception


if __name__ == '__main__':
    from time import sleep


    def x_sleep():
        print("sleep_start")
        sleep(15)
        print("sleep_stop")


    class TestE(Exception):
        def __init__(self, message='TestException'):
            super().__init__(message)

    def y_exception():
        raise TestE()


    mp = MappingClass()

    pad = X5Pad(mp)

    pi = EvdevDeviceInput()

    mp.map_standard_action("test", x_sleep)
    mp.map_standard_action("movement", lambda x, y: print(int(x), int(y * 100)))
    mp.map_standard_action("up", y_exception)
    mp.map_standard_action("down", lambda: print("test a"))
    mp.map_standard_action("exit", lambda: print("exit"))

    pad.map_joystick("LEFT_J", "movement", action_type="ang_str")
    pad.map_key("BTN_Y", "up")
    pad.map_key("BTN_A", "down")
    pad.map_key("BTN_X", "test")
    pad.map_key("BTN_SELECT", "exit")

    pi.set_ActionError_feedback(lambda x: print(x))
    pi.set_additional_exception(TestE)

    pi.add_device(pad, 1)
    pi.connect_devices()

    pi.listen_and_execute_one_dev()

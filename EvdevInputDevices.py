from abc import ABC
from typing import Optional, Callable, Dict

from evdev import InputDevice, categorize, ecodes, KeyEvent, SynEvent, AbsEvent, list_devices, InputEvent

from InputMappings.InputErrors import ActionError, DeviceNotPluggedError, NonExistingInputError
from MappingClass import Mapping

from numpy import rad2deg
from math import atan2, sqrt


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

        self.execute_action = (_ for _ in ()).throw(ActionError())

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

    def execute_action_ang_str(self) -> None:
        """
        Execute action from mapped mapping, with angle and strength as passed params
        """
        if self.mapping_to_execute is None:
            raise ActionError()

        while abs(self.last_pos_xy[0]) > self.thresholds or abs(self.last_pos_xy[1]) > self.thresholds:
            # TODO - Zrobić whilea tak jakby tablicowo

            x_j, y_j = self.last_pos_xy[0], -self.last_pos_xy[1]
            # print(x_j, y_j, spec_arctan(x_j, y_j), sqrt(x_j ** 2 + y_j ** 2))
            # TODO - wywalić tego mina
            self.mapping_to_execute.executeAction(rad2deg(atan2(x_j, y_j)), min(sqrt(x_j ** 2 + y_j ** 2), 1))

    def execute_action_x_y(self) -> None:
        if self.mapping_to_execute is None:
            raise ActionError()

        while abs(self.last_pos_xy[0]) > self.thresholds or abs(self.last_pos_xy[1]) > self.thresholds:
            # TODO - Zrobić whilea tak jakby tablicowo
            x_j, y_j = self.last_pos_xy[0], self.last_pos_xy[1]
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

    def connect(self) -> None:
        """
        Connect device;
        :raise DeviceNotPlugged: raised, when device is not plugged in.
        """
        for path in list_devices():
            print(InputDevice(path).name)
            if InputDevice(path).name == self.name:
                self.connected = True
                print("connected")
                self.device = InputDevice(path)
                break
        else:
            raise DeviceNotPluggedError()

    def update_joysticks_states(self, input_event: KeyEvent) -> None:
        """
        update states of all joysticks on device (current tilt, angle etc.)
        :param input_event - input event that is being red in order to update proper input state.
        """
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

    def update_keys_states(self, input_event: AbsEvent) -> None:
        """
        update states of all buttons on device (whether they are pressed, released etc.)
        :param input_event - input event that is being red in order to update proper input state.
        """
        ev_name = input_event.keycode
        ev_state = input_event.keystate
        for i in self.buttons_list:
            clicked_button = i.update_single_button(ev_name, ev_state)
            if clicked_button is not None:
                return clicked_button

    def update_states(self, input_event: InputEvent) -> Optional[Callable[[InputEvent], Optional[EvdevInput]]]:
        """
        update states of buttons, joysticks, etc (whether they are pressed, tilted, released etc.)
        :param input_event - input event that is being red in order to update proper input state.
        """
        for input_type, proper_update_function in self.instance_check_dict.items():
            if isinstance(input_event, input_type):
                if input_type in self.capabilities:
                    return proper_update_function(input_event)

        return None

    def map_key(self, keyInput: str, actionName: str, keyState: int = 1) -> None:
        """
        Map standard action from mapping class to button
        :param keyInput: name of button on pad
        :param actionName: name of standard action event in relative mapping object
        :param keyState: whether event should be executed on press (1), constantly while button is pressed (2)
                        or on release (0)
        :return: None
        """
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
                raise NonExistingInputError()
        else:
            raise IndexError(f"First map the action named {actionName}!")

    def map_joystick(self, joystick_input: str, axisName: str, action_type: str) -> None:
        """
        Map standard action from mapping class to joystick
        :param joystick_input: name of joystick on pad
        :param axisName: name of standard action event in relative mapping object
        :param action_type: "ang_str" or "x_y", depending whether you want
                            arguments to be passed as angle and strength or x and y
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
                raise NonExistingInputError()
        else:
            raise IndexError(f"First map the axis named {axisName}!")

    def listen_loop(self, stop_name: str, stop_state: int, target) -> None:
        """
        Create infinite loop to listen to this device input, and set executing_button and executing_joystick variables
        of a target
        :param stop_name
        :param stop_state
        :param target: instance of EvdevDeviceInput, that have variables executing_button and executing_joystick, that
        are being set while loop is on.
        """

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



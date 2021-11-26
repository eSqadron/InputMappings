import json
import threading
import time
from typing import Optional, Dict, Callable, Type

from EvdevInputDevices import Joystick, Button, EvdevDevice
from InputErrors import PlaceholderException, DeviceNotPluggedError, NoDevicesAddedError, ActionError
from MappingClass import MappingClass


class EvdevDeviceInput:
    def __init__(self):
        self.keyActionBindings = {}

        self.to_exec: Optional[MappingClass] = None
        self.executing_joystick: Optional[Joystick] = None
        self.executing_button: Optional[Button] = None

        self.stopKeyName = "BTN_SELECT"  # TODO ogarnąć żeby to modyfikowalne było

        # priority -> device
        self.devices: Dict[int, EvdevDevice] = {}

        self.on_ActionError: Optional[Callable] = None

        self.additional_exception = PlaceholderException

    def add_device(self, device: EvdevDevice, priority: int, overwrite=False) -> None:
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

    def connect_devices(self) -> None:
        """
        Try to connect to all added devices, in ascending priority
        :return: None
        """
        connected = False
        for p, d in sorted(self.devices.items()):
            for i in range(10):
                try:
                    d.connect()
                except DeviceNotPluggedError:
                    time.sleep(1)
                    continue
                else:
                    print("device found")
                    connected = True
                    break
            else:
                print("couldn't find device!")

        if not connected:
            raise DeviceNotPluggedError()

    def get_primary_device(self, only_connected: bool = True) -> EvdevDevice:
        """
        Get current primary device (with highest priority (lowest number))
        :param only_connected: search only connected devices (bool)
        """
        if not only_connected:
            return sorted(self.devices.items())[0][1]

        for p, d in sorted(self.devices.items()):
            if d.connected:
                return d

        raise NoDevicesAddedError()

    def listen_and_execute_one_dev(self, device: Optional[EvdevDevice] = None) -> None:
        if device is None:
            device = self.get_primary_device()
        padInputThread = threading.Thread(target=device.listen_loop, args=(self.stopKeyName, 0, self))
        padInputThread.start()

        while padInputThread.is_alive():
            for executing_input in [self.executing_joystick, self.executing_button]:
                if executing_input is not None:
                    #if executing_input.execute_action is not None:
                    try:
                        executing_input.execute_action()
                    except ActionError as ae:
                        if self.on_ActionError is None:
                            pass
                        else:
                            self.on_ActionError(ae)
                    except self.additional_exception as ae:
                        if self.on_ActionError is None:
                            pass
                        else:
                            self.on_ActionError(ae)

            self.executing_joystick = None
            self.executing_button = None

    def listen_and_execute_all(self) -> None:
        pass
        # TODO - ogarnąć to

    def set_ActionError_feedback(self, rapport_function: Callable[[Exception], None]) -> None:
        """
        Set function that will rapport when button that is not mapped was pressed
        :param rapport_function: function that gives user feedback about error (for example log or print of sorts)
        """
        self.on_ActionError = rapport_function

    def set_additional_exception(self, exception: Type[Exception]) -> None:
        """
        During mapped function execution some additional exceptions might occur. If they derive from one class, you may
        set up this parameter to catch them inside this loop.
        :param exception: derivative of Exception, to be caught in the loop
        """
        self.additional_exception = exception

    def load_from_json(self, file_path: str, mapping_object, gamepad) -> None:
        """
        Load all devices from json file
        file structure:
        {
          "gamepads": {
              "priority": X,
              "keys": {
                "KEY_NAME1": "mapping_name1",
                "KEY_NAME2": "mapping_name2",
              },
              "joysticks": {
                "J_NAME1": [
                  "mapping_name",
                  "action_type (ang_str for example)"
                ],
                "J_NAME2": [
                  "mapping_name3",
                  "action_type (ang_str for example)"
                ]
              }
        }
        :param file_path: path to file to be loaded
        :param mapping_object: mapping object, with relation to which devices map their buttons
        """
        f = open(file_path)
        data = json.load(f)

        try:
            gp = data["gamepads"]
        except KeyError:
            pass
        else:
            for gp_name, gp_values in gp.items():
                if gp_name == gamepad.name:
                    print(gp_name)
                    new_device = gamepad
                    try:
                        gp_keys = gp_values["keys"]
                    except KeyError:
                        pass
                    else:
                        for key_name, map_name in gp_keys.items():
                            new_device.map_key(key_name, map_name)

                    try:
                        gp_j = gp_values["joysticks"]
                    except KeyError:
                        pass
                    else:
                        for j_name, map_name_v in gp_j.items():
                            new_device.map_joystick(j_name, map_name_v[0], action_type=map_name_v[1])

                    self.add_device(new_device, gp_values['priority'])


if __name__ == '__main__':
    from time import sleep
    from EvdevInputDevices import x360Pad


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

    pad = x360Pad(mp)

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

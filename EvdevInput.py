import threading
from queue import Queue

from typing import Dict, List, Tuple, Set
import evdev as ev

from MappingClass import MappingClass


class EvdevDevicesError(Exception):
    def __init__(self, message='Problem with Device!'):
        super().__init__(message)


class EvdevDeviceInput:
    def __init__(self, related_mapping: MappingClass, mode="queued"):
        self.button_binds: Dict[str, Tuple[str, int]] = {}
        self.joystick_binds: Dict[str, Tuple[str, str]] = {}

        self.related_mapping: MappingClass = related_mapping
        self.maps_to_execute_queue = Queue()

        self.pressed_buttons: Set[str] = set()
        self.tilted_joysticks: Dict[str, float] = {}

        self.joystick_threshold = 0.3

        self.mode = mode
        self.executing = False
#
#         self.paused = False
#         self.waiting_lock = threading.RLock()
#         self.waiting_cond = threading.Condition(self.waiting_lock)
#
#
#     def pause(self):
#         self.paused = True
# #         print("locking")
#         self.waiting_lock.acquire()
# #         print("locked")
#         while self.paused:
#             self.waiting_cond.wait()
#         self.waiting_lock.release()
#
#     def resume(self):
#         self.paused = False
#         self.waiting_lock.acquire()
#         self.waiting_cond.notify_all()
# #         try:
# #             self.waiting_cond.notify_all()
# #         except RuntimeError:
# #             pass
#         self.waiting_lock.release()
#
    
    def push_button_on_queue(self, action_name):
        mapping = self.related_mapping.standard_mappings[action_name]
        if self.mode == "queued":
            self.maps_to_execute_queue.put(mapping.executeAction)
        elif self.mode == "one_action_at_the_time":
            if self.maps_to_execute_queue.empty() and (not self.executing):
                self.maps_to_execute_queue.put(mapping.executeAction)

    def push_abs_on_queue(self, action_name, x_value, y_value):
        mapping = self.related_mapping.standard_mappings[action_name]
        if self.mode == "queued":
            self.maps_to_execute_queue.put(lambda: mapping.executeAction(x=x_value, y=y_value))
        elif self.mode == "one_action_at_the_time":
            if self.maps_to_execute_queue.empty() and (not self.executing):
                self.maps_to_execute_queue.put(lambda: mapping.executeAction(x=x_value, y=y_value))

    def normalize_ABS(self, current_device: ev.device, axis: str, x: int) -> float:
        dev_infos = current_device.capabilities(verbose=True, absinfo=True)[('EV_ABS', 3)]
        for key, dev_info in dev_infos:
            if key[0] == axis:
                break
        else:
            raise EvdevDevicesError(f"plugged devices don't have {axis} ABS event")

        x_max = dev_info.max
        x_min = dev_info.min
        return (x - x_min) / (x_max - x_min) * 2 - 1

    def listen_and_push(self) -> None:
        """
        Read actions from all devices and push them to self.maps_to_execute_queue FIFO queue
        """
        plugged_devices = self.__get_plugged_devices_list()  # TODO - make list refreshable
        while True:
            # Take care of already pushed buttons (action that happen in loop while button is held)
            for button_name in self.pressed_buttons:
                for action_name, value in self.button_binds.items():
                    if button_name == value[0] and value[1] == 2:
                        self.push_button_on_queue(action_name)

            for action_name, value in self.joystick_binds.items():
                x = 0
                y = 0
                if value[0] in self.tilted_joysticks.keys():
                    x = self.tilted_joysticks[value[0]]
                if value[1] in self.tilted_joysticks.keys():
                    y = self.tilted_joysticks[value[1]]

                if abs(x) > self.joystick_threshold or abs(y) > self.joystick_threshold:
                    self.push_abs_on_queue(action_name, x, y)

            # Check for new pushed buttons (press or release) or other changed states (like moved joysticks)
            for device in plugged_devices:
                event = device.read_one()
                if event is not None:
                    ev_name_list = []
                    ev_names = []
                    if event.type == ev.ecodes.EV_KEY:
                        ev_names = ev.ecodes.keys[event.code]
                    elif event.type == ev.ecodes.EV_ABS:
                        ev_names = ev.ecodes.ABS[event.code]

                    if isinstance(ev_names, List):
                        ev_name_list.extend(ev_names)
                    else:
                        ev_name_list.append(ev_names)
                        # and iterate over it:
                    for ev_name in ev_name_list:
                        # for every name of a button clicked:
                        ###############################################
                        if event.type == ev.ecodes.EV_KEY:  # if event is a button/key:
                            for action_name, value in self.button_binds.items():
                                if value[0] == ev_name:
                                    # if this specific key (or joystick etc.) name is defined (we have action bound
                                    # to it)
                                    if value[1] == event.value:
                                        # if value is correct (mostly pressed or released)
                                        # put proper mapping to queue to be executed
                                        self.push_button_on_queue(action_name)

                                # add currently pressed button to self.pressed_buttons (later it will help with hold
                                # events)
                                if event.value == 1:
                                    self.pressed_buttons.add(ev_name)
                                if event.value == 0:
                                    if ev_name in self.pressed_buttons:
                                        self.pressed_buttons.remove(ev_name)
                        #############################################
                        elif event.type == ev.ecodes.EV_ABS:  # if event is a joystick:
                            for action_name, value in self.joystick_binds.items():
                                input_tilt = self.normalize_ABS(device, ev_name, event.value)
                                if value[0] == ev_name:
                                    self.tilted_joysticks[value[0]] = input_tilt
                                    if value[1] not in self.tilted_joysticks.keys():
                                        self.tilted_joysticks[value[1]] = 0
                                    self.push_abs_on_queue(action_name, self.tilted_joysticks[value[0]],
                                                           self.tilted_joysticks[value[1]])
                                    return
                                elif value[1] == ev_name:
                                    self.tilted_joysticks[value[1]] = input_tilt
                                    if value[0] not in self.tilted_joysticks.keys():
                                        self.tilted_joysticks[value[0]] = 0
                                    self.push_abs_on_queue(action_name, self.tilted_joysticks[value[0]],
                                                           self.tilted_joysticks[value[1]])
                                    return

    def __get_plugged_devices_list(self) -> List[ev.device.InputDevice]:
        """
        List all plugged devices.
        """
        return [ev.InputDevice(path) for path in ev.list_devices()]

    def run(self):
        """
        Open another thread that will run self.listen_and_push function
        """
        padInputThread = threading.Thread(target=self.listen_and_push, args=())
        padInputThread.start()

    def bind_EV_KEY(self, action_name, ev_key_name, ev_key_state=1, args=None, kwargs=None):
        """
        bind specific actions names to (key_name, key_state) tuple
        """
        if kwargs is None:
            kwargs = {}
        if args is None:
            args = []

        if action_name in self.related_mapping.standard_mappings.keys():
            if ev_key_name in self.get_EV_KEYs():
                self.button_binds[action_name] = (ev_key_name, ev_key_state)
            else:
                EvdevDevicesError(f"Key {ev_key_name} doesn't exist!")
        else:
            EvdevDevicesError(f"action {action_name} isn't mapped!")

    def get_EV_KEYs(self, all_EV_KEYs: bool = True) -> List[str]:
        if all_EV_KEYs:
            t = list(ev.ecodes.keys.values())
        else:
            t = []
            for device in self.__get_plugged_devices_list():
                t.extend([i for i, j in device.capabilities(verbose=True)[('EV_KEY', 1)]])

        full_list = []
        for sublist in t:
            if isinstance(sublist, str):
                full_list.append(sublist)
            else:
                for item in sublist:
                    full_list.append(item)

        return full_list

    def bind_double_EV_ABS(self, action_name, ev_abs_x_name, ev_abs_y_name, args=None, kwargs=None):
        if kwargs is None:
            kwargs = {}
        if args is None:
            args = []

        if action_name in self.related_mapping.standard_mappings.keys():
            if ev_abs_x_name in self.get_EV_ABSs() and ev_abs_y_name in self.get_EV_ABSs():
                self.joystick_binds[action_name] = (ev_abs_x_name, ev_abs_y_name)
            else:
                EvdevDevicesError(f"ABS axis {ev_abs_x_name} or {ev_abs_y_name} doesn't exist!")
        else:
            EvdevDevicesError(f"action {action_name} isn't mapped!")

    def get_EV_ABSs(self):
        return list(ev.ecodes.ABS.values())


if __name__ == '__main__':
    from time import sleep

    mp = MappingClass()

    pi = EvdevDeviceInput(mp, mode="one_action_at_the_time")

    print(pi.get_EV_KEYs(all_EV_KEYs=False))


    def x_start():
        print("start")
        # pass


    def x_held():
        print("holding")
        # pass


    def x_stop():
        print("stopping")
        # pass


    def x_sleep():
        print("sleep_start")
        sleep(15)
        print("sleep_stop")


    def j_test(x, y):
        print(x, y)
        # pass


    mp.map_standard_action("test", x_sleep)
    mp.map_standard_action("test_start", x_start)
    mp.map_standard_action("test_hold", x_held)
    mp.map_standard_action("test_stop", x_stop)

    mp.map_standard_action("j_test", j_test)

    pi.bind_EV_KEY("test", "BTN_Y", 1)

    pi.bind_EV_KEY("test_start", "BTN_X", 1)
    pi.bind_EV_KEY("test_stop", "BTN_X", 0)
    pi.bind_EV_KEY("test_hold", "BTN_X", 2)

    pi.bind_double_EV_ABS("j_test", "ABS_X", "ABS_Y")

    pi.run()
    while True:
        if not pi.maps_to_execute_queue.empty():
            pi.executing = True
            fcn = pi.maps_to_execute_queue.get_nowait()
            fcn()
            pi.executing = False

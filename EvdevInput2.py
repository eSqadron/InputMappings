from typing import Optional

import evdev as ev

from InputErrors import DeviceError, ActionError
from MappingClass import Mapping


class UnknownDeviceError(DeviceError):
    def __init__(self, message='Unknown Device'):
        super().__init__(message)


class SingleInput:
    pass


class Slider(SingleInput):
    def __init__(self, name):
        self.name = name


class Button(SingleInput):
    def __init__(self, name: str):
        self.name = name
        self.mapping_to_execute_on_press = None
        self.mapping_to_while_pressed = None
        self.mapping_to_execute_on_release = None

        self.is_pressed = False

    def update_single_button(self, ev_name, ev_val):
        pass
        # found = False
        # if isinstance(ev_name, list):
        #     if self.ev_name in ev_name:
        #         found = True
        # elif isinstance(ev_name, str):
        #     if ev_name == self.ev_name:
        #         found = True
        #
        # if found:
        #     if ev_val == 1:
        #         self.is_pressed = True
        #     elif ev_val == 0:
        #         self.is_pressed = False
        #
        #     return self
        #
        # else:
        #     return None

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


class Device:
    def __init__(self, device: ev.device.InputDevice):
        self.ev_device = device
        self.type = 'unknown'

        # self.syn_ev_0 = []
        # self.key_ev_1 = []
        # self.abs_ev_2 = []
        # self.rel_ev_3 = []
        # self.msc_ev_4 = []
        #
        # self.events = [self.syn_ev_0, self.key_ev_1, self.abs_ev_2, self.rel_ev_3, self.msc_ev_4]

        self.buttons = []
        self.joysticks = []
        self.sliders = []

        # TODO - cała lista nieprzydzielonych przycisków

        self.possible_event_types = []

        c = device.capabilities()

        for code in c:
            self.possible_event_types.append(code)

        if all(x in self.possible_event_types for x in [1, 2, 4]):
            if all(x in c[1] for x in [272, 273, 274]) and all(x in c[2] for x in [0, 1, 8]):
                self.type = 'mouse'

                for x in [272, 273, 274]:
                    ev_name = ev.ecodes.KEY[x]
                    if isinstance(ev_name, list):
                        ev_name = ev_name[0]

                    self.buttons.append(Button(ev_name))

                for x in [0, 1, 8]:
                    ev_name = ev.ecodes.KEY[x]
                    if isinstance(ev_name, list):
                        ev_name = ev_name[0]

                    self.sliders.append(Slider(ev_name))


class RunDevices:
    def __init__(self):
        self.bad_devices = []
        self.good_devices = []

    def scan_devices(self):
        bad_devices_temp = []
        good_devices_temp = []
        for device in [ev.InputDevice(path) for path in ev.list_devices()]:
            try:
                categorise_device(device)
            except UnknownDeviceError():
                bad_devices_temp.append(device)
            else:
                good_devices_temp.append(device)

        self.bad_devices = bad_devices_temp
        self.good_devices = good_devices_temp

    # def connect_all(self):
    #     for self.good_devices


"""
[(['BTN_LEFT', 'BTN_MOUSE'], 272), ('BTN_RIGHT', 273), ('BTN_MIDDLE', 274), ('BTN_SIDE', 275), ('BTN_EXTRA', 276), ('BTN_FORWARD', 277), ('BTN_BACK', 278), ('BTN_TASK', 279)]
[('REL_X', 0), ('REL_Y', 1), ('REL_HWHEEL', 6), ('REL_WHEEL', 8), ('?', 11), ('?', 12)]
[('MSC_SCAN', 4)]
"""
"""
{('EV_SYN', 0): [('SYN_REPORT', 0), ('SYN_CONFIG', 1), ('SYN_MT_REPORT', 2), ('SYN_DROPPED', 3), ('?', 4)], ('EV_KEY', 1): [('KEY_ESC', 1), ('KEY_ENTER', 28), ('KEY_KPMINUS', 74), ('KEY_KPPLUS', 78), ('KEY_UP', 103), ('KEY_LEFT', 105), ('KEY_RIGHT', 106), ('KEY_DOWN', 108), ('KEY_INSERT', 110), ('KEY_DELETE', 111), (['KEY_MIN_INTERESTING', 'KEY_MUTE'], 113), ('KEY_VOLUMEDOWN', 114), ('KEY_VOLUMEUP', 115), ('KEY_POWER', 116), ('KEY_PAUSE', 119), ('KEY_SCALE', 120), ('KEY_STOP', 128), ('KEY_PROPS', 130), ('KEY_UNDO', 131), ('KEY_COPY', 133), ('KEY_OPEN', 134), ('KEY_PASTE', 135), ('KEY_FIND', 136), ('KEY_CUT', 137), ('KEY_HELP', 138), ('KEY_MENU', 139), ('KEY_CALC', 140), ('KEY_SLEEP', 142), ('KEY_WAKEUP', 143), ('KEY_FILE', 144), ('KEY_WWW', 150), (['KEY_COFFEE', 'KEY_SCREENLOCK'], 152), ('KEY_MAIL', 155), ('KEY_BOOKMARKS', 156), ('KEY_BACK', 158), ('KEY_FORWARD', 159), ('KEY_EJECTCD', 161), ('KEY_NEXTSONG', 163), ('KEY_PLAYPAUSE', 164), ('KEY_PREVIOUSSONG', 165), ('KEY_STOPCD', 166), ('KEY_RECORD', 167), ('KEY_REWIND', 168), ('KEY_PHONE', 169), ('KEY_CONFIG', 171), ('KEY_HOMEPAGE', 172), ('KEY_REFRESH', 173), ('KEY_EXIT', 174), ('KEY_EDIT', 176), ('KEY_SCROLLUP', 177), ('KEY_SCROLLDOWN', 178), ('KEY_NEW', 181), ('KEY_REDO', 182), ('KEY_CLOSE', 206), ('KEY_PLAY', 207), ('KEY_FASTFORWARD', 208), ('KEY_BASSBOOST', 209), ('KEY_PRINT', 210), ('KEY_CAMERA', 212), ('KEY_CHAT', 216), ('KEY_SEARCH', 217), ('KEY_FINANCE', 219), ('KEY_CANCEL', 223), ('KEY_BRIGHTNESSDOWN', 224), ('KEY_BRIGHTNESSUP', 225), ('KEY_KBDILLUMTOGGLE', 228), ('KEY_KBDILLUMDOWN', 229), ('KEY_KBDILLUMUP', 230), ('KEY_SEND', 231), ('KEY_REPLY', 232), ('KEY_FORWARDMAIL', 233), ('KEY_SAVE', 234), ('KEY_DOCUMENTS', 235), ('KEY_UNKNOWN', 240), ('KEY_VIDEO_NEXT', 241), (['KEY_BRIGHTNESS_AUTO', 'KEY_BRIGHTNESS_ZERO'], 244), (['BTN_0', 'BTN_MISC'], 256), (['BTN_LEFT', 'BTN_MOUSE'], 272), ('BTN_RIGHT', 273), ('BTN_MIDDLE', 274), ('BTN_SIDE', 275), ('BTN_EXTRA', 276), ('KEY_SELECT', 353), ('KEY_GOTO', 354), ('KEY_INFO', 358), ('KEY_PROGRAM', 362), ('KEY_PVR', 366), ('KEY_SUBTITLE', 370), ('KEY_ZOOM', 372), ('KEY_KEYBOARD', 374), ('KEY_SCREEN', 375), ('KEY_PC', 376), ('KEY_TV', 377), ('KEY_TV2', 378), ('KEY_VCR', 379), ('KEY_VCR2', 380), ('KEY_SAT', 381), ('KEY_CD', 383), ('KEY_TAPE', 384), ('KEY_TUNER', 386), ('KEY_PLAYER', 387), ('KEY_DVD', 389), ('KEY_AUDIO', 392), ('KEY_VIDEO', 393), ('KEY_MEMO', 396), ('KEY_CALENDAR', 397), ('KEY_RED', 398), ('KEY_GREEN', 399), ('KEY_YELLOW', 400), ('KEY_BLUE', 401), ('KEY_CHANNELUP', 402), ('KEY_CHANNELDOWN', 403), ('KEY_LAST', 405), ('KEY_NEXT', 407), ('KEY_RESTART', 408), ('KEY_SLOW', 409), ('KEY_SHUFFLE', 410), ('KEY_PREVIOUS', 412), ('KEY_VIDEOPHONE', 416), ('KEY_GAMES', 417), ('KEY_ZOOMIN', 418), ('KEY_ZOOMOUT', 419), ('KEY_ZOOMRESET', 420), ('KEY_WORDPROCESSOR', 421), ('KEY_EDITOR', 422), ('KEY_SPREADSHEET', 423), ('KEY_GRAPHICSEDITOR', 424), ('KEY_PRESENTATION', 425), ('KEY_DATABASE', 426), ('KEY_NEWS', 427), ('KEY_VOICEMAIL', 428), ('KEY_ADDRESSBOOK', 429), ('KEY_MESSENGER', 430), (['KEY_BRIGHTNESS_TOGGLE', 'KEY_DISPLAYTOGGLE'], 431), ('KEY_SPELLCHECK', 432), ('KEY_LOGOFF', 433), ('KEY_MEDIA_REPEAT', 439), ('KEY_IMAGES', 442), ('KEY_BUTTONCONFIG', 576), ('KEY_TASKMANAGER', 577), ('KEY_JOURNAL', 578), ('KEY_CONTROLPANEL', 579), ('KEY_APPSELECT', 580), ('KEY_SCREENSAVER', 581), ('KEY_VOICECOMMAND', 582), ('KEY_ASSISTANT', 583), ('?', 584), ('?', 585), ('KEY_BRIGHTNESS_MIN', 592), ('KEY_BRIGHTNESS_MAX', 593), ('KEY_KBDINPUTASSIST_PREV', 608), ('KEY_KBDINPUTASSIST_NEXT', 609), ('KEY_KBDINPUTASSIST_PREVGROUP', 610), ('KEY_KBDINPUTASSIST_NEXTGROUP', 611), ('KEY_KBDINPUTASSIST_ACCEPT', 612), ('KEY_KBDINPUTASSIST_CANCEL', 613)], ('EV_REL', 2): [('REL_X', 0), ('REL_Y', 1), ('REL_HWHEEL', 6), ('REL_WHEEL', 8), ('?', 11), ('?', 12)], ('EV_ABS', 3): [(('ABS_VOLUME', 32), AbsInfo(value=0, min=0, max=12287, fuzz=0, flat=0, resolution=0))], ('EV_MSC', 4): [('MSC_SCAN', 4)]}
"""

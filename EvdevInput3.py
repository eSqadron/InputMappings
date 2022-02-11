"""
[(['BTN_LEFT', 'BTN_MOUSE'], 272), ('BTN_RIGHT', 273), ('BTN_MIDDLE', 274), ('BTN_SIDE', 275), ('BTN_EXTRA', 276), ('BTN_FORWARD', 277), ('BTN_BACK', 278), ('BTN_TASK', 279)]
[('REL_X', 0), ('REL_Y', 1), ('REL_HWHEEL', 6), ('REL_WHEEL', 8), ('?', 11), ('?', 12)]
[('MSC_SCAN', 4)]
"""
import threading
from queue import Queue

from typing import Dict, List, Tuple
import evdev as ev

from MappingClass import MappingClass, Mapping

"""
{('EV_SYN', 0): [('SYN_REPORT', 0), ('SYN_CONFIG', 1), ('SYN_MT_REPORT', 2), ('SYN_DROPPED', 3), ('?', 4)], ('EV_KEY', 1): [('KEY_ESC', 1), ('KEY_ENTER', 28), ('KEY_KPMINUS', 74), ('KEY_KPPLUS', 78), ('KEY_UP', 103), ('KEY_LEFT', 105), ('KEY_RIGHT', 106), ('KEY_DOWN', 108), ('KEY_INSERT', 110), ('KEY_DELETE', 111), (['KEY_MIN_INTERESTING', 'KEY_MUTE'], 113), ('KEY_VOLUMEDOWN', 114), ('KEY_VOLUMEUP', 115), ('KEY_POWER', 116), ('KEY_PAUSE', 119), ('KEY_SCALE', 120), ('KEY_STOP', 128), ('KEY_PROPS', 130), ('KEY_UNDO', 131), ('KEY_COPY', 133), ('KEY_OPEN', 134), ('KEY_PASTE', 135), ('KEY_FIND', 136), ('KEY_CUT', 137), ('KEY_HELP', 138), ('KEY_MENU', 139), ('KEY_CALC', 140), ('KEY_SLEEP', 142), ('KEY_WAKEUP', 143), ('KEY_FILE', 144), ('KEY_WWW', 150), (['KEY_COFFEE', 'KEY_SCREENLOCK'], 152), ('KEY_MAIL', 155), ('KEY_BOOKMARKS', 156), ('KEY_BACK', 158), ('KEY_FORWARD', 159), ('KEY_EJECTCD', 161), ('KEY_NEXTSONG', 163), ('KEY_PLAYPAUSE', 164), ('KEY_PREVIOUSSONG', 165), ('KEY_STOPCD', 166), ('KEY_RECORD', 167), ('KEY_REWIND', 168), ('KEY_PHONE', 169), ('KEY_CONFIG', 171), ('KEY_HOMEPAGE', 172), ('KEY_REFRESH', 173), ('KEY_EXIT', 174), ('KEY_EDIT', 176), ('KEY_SCROLLUP', 177), ('KEY_SCROLLDOWN', 178), ('KEY_NEW', 181), ('KEY_REDO', 182), ('KEY_CLOSE', 206), ('KEY_PLAY', 207), ('KEY_FASTFORWARD', 208), ('KEY_BASSBOOST', 209), ('KEY_PRINT', 210), ('KEY_CAMERA', 212), ('KEY_CHAT', 216), ('KEY_SEARCH', 217), ('KEY_FINANCE', 219), ('KEY_CANCEL', 223), ('KEY_BRIGHTNESSDOWN', 224), ('KEY_BRIGHTNESSUP', 225), ('KEY_KBDILLUMTOGGLE', 228), ('KEY_KBDILLUMDOWN', 229), ('KEY_KBDILLUMUP', 230), ('KEY_SEND', 231), ('KEY_REPLY', 232), ('KEY_FORWARDMAIL', 233), ('KEY_SAVE', 234), ('KEY_DOCUMENTS', 235), ('KEY_UNKNOWN', 240), ('KEY_VIDEO_NEXT', 241), (['KEY_BRIGHTNESS_AUTO', 'KEY_BRIGHTNESS_ZERO'], 244), (['BTN_0', 'BTN_MISC'], 256), (['BTN_LEFT', 'BTN_MOUSE'], 272), ('BTN_RIGHT', 273), ('BTN_MIDDLE', 274), ('BTN_SIDE', 275), ('BTN_EXTRA', 276), ('KEY_SELECT', 353), ('KEY_GOTO', 354), ('KEY_INFO', 358), ('KEY_PROGRAM', 362), ('KEY_PVR', 366), ('KEY_SUBTITLE', 370), ('KEY_ZOOM', 372), ('KEY_KEYBOARD', 374), ('KEY_SCREEN', 375), ('KEY_PC', 376), ('KEY_TV', 377), ('KEY_TV2', 378), ('KEY_VCR', 379), ('KEY_VCR2', 380), ('KEY_SAT', 381), ('KEY_CD', 383), ('KEY_TAPE', 384), ('KEY_TUNER', 386), ('KEY_PLAYER', 387), ('KEY_DVD', 389), ('KEY_AUDIO', 392), ('KEY_VIDEO', 393), ('KEY_MEMO', 396), ('KEY_CALENDAR', 397), ('KEY_RED', 398), ('KEY_GREEN', 399), ('KEY_YELLOW', 400), ('KEY_BLUE', 401), ('KEY_CHANNELUP', 402), ('KEY_CHANNELDOWN', 403), ('KEY_LAST', 405), ('KEY_NEXT', 407), ('KEY_RESTART', 408), ('KEY_SLOW', 409), ('KEY_SHUFFLE', 410), ('KEY_PREVIOUS', 412), ('KEY_VIDEOPHONE', 416), ('KEY_GAMES', 417), ('KEY_ZOOMIN', 418), ('KEY_ZOOMOUT', 419), ('KEY_ZOOMRESET', 420), ('KEY_WORDPROCESSOR', 421), ('KEY_EDITOR', 422), ('KEY_SPREADSHEET', 423), ('KEY_GRAPHICSEDITOR', 424), ('KEY_PRESENTATION', 425), ('KEY_DATABASE', 426), ('KEY_NEWS', 427), ('KEY_VOICEMAIL', 428), ('KEY_ADDRESSBOOK', 429), ('KEY_MESSENGER', 430), (['KEY_BRIGHTNESS_TOGGLE', 'KEY_DISPLAYTOGGLE'], 431), ('KEY_SPELLCHECK', 432), ('KEY_LOGOFF', 433), ('KEY_MEDIA_REPEAT', 439), ('KEY_IMAGES', 442), ('KEY_BUTTONCONFIG', 576), ('KEY_TASKMANAGER', 577), ('KEY_JOURNAL', 578), ('KEY_CONTROLPANEL', 579), ('KEY_APPSELECT', 580), ('KEY_SCREENSAVER', 581), ('KEY_VOICECOMMAND', 582), ('KEY_ASSISTANT', 583), ('?', 584), ('?', 585), ('KEY_BRIGHTNESS_MIN', 592), ('KEY_BRIGHTNESS_MAX', 593), ('KEY_KBDINPUTASSIST_PREV', 608), ('KEY_KBDINPUTASSIST_NEXT', 609), ('KEY_KBDINPUTASSIST_PREVGROUP', 610), ('KEY_KBDINPUTASSIST_NEXTGROUP', 611), ('KEY_KBDINPUTASSIST_ACCEPT', 612), ('KEY_KBDINPUTASSIST_CANCEL', 613)], ('EV_REL', 2): [('REL_X', 0), ('REL_Y', 1), ('REL_HWHEEL', 6), ('REL_WHEEL', 8), ('?', 11), ('?', 12)], ('EV_ABS', 3): [(('ABS_VOLUME', 32), AbsInfo(value=0, min=0, max=12287, fuzz=0, flat=0, resolution=0))], ('EV_MSC', 4): [('MSC_SCAN', 4)]}
"""


class EvdevDeviceInput:
    def __init__(self, related_mapping: MappingClass):
        self.binds: Dict[str, Tuple[Mapping, int]] = {}
        self.related_mapping = related_mapping

        self.maps_to_execute_queue = Queue()

        # TODO - przerobić na każde urządzenie
        self.device = None
        for path in ev.list_devices():
            print(ev.InputDevice(path).name)
            if ev.InputDevice(path).name == "Xbox 360 Wireless Receiver":
                print("connected")
                self.device = ev.InputDevice(path)

    def listen_and_push(self):
        # TODO - przerobić na każde urządzenie
        while True:
            event = self.device.read_one()
            if event is not None:
                ev_name_list = ev.ecodes.BTN[event.code]
                if not isinstance(ev_name_list, List):
                    ev_name_list = [ev_name_list]
                for ev_name in ev_name_list:
                    try:
                        if self.binds[ev_name][1] == event.value:
                            self.maps_to_execute_queue.put(self.binds[ev_name][0])
                    except KeyError:
                        pass

    def run(self):
        padInputThread = threading.Thread(target=self.listen_and_push, args=())
        padInputThread.start()

    def bind_EV_KEY(self, map_name, ev_key_name, ev_key_state=1):
        if map_name in self.related_mapping.standard_mappings.keys():
            if ev_key_name in self.get_EV_KEYs():
                self.binds[ev_key_name] = (self.related_mapping.standard_mappings[map_name], ev_key_state)

    def get_EV_KEYs(self, all_EV_KEYs: int = 1) -> List:
        if all_EV_KEYs:
            t = list(ev.ecodes.KEY.values())
        else:
            t = []  # TODO - tylko z podpiętych urządzeń

        full_list = []
        for sublist in t:
            if isinstance(sublist, str):
                full_list.append(sublist)
            else:
                for item in sublist:
                    full_list.append(item)

        return full_list


if __name__ == '__main__':
    from time import sleep

    mp = MappingClass()

    pi = EvdevDeviceInput(mp)
    def x_sleep():
        print("sleep_start")
        sleep(15)
        print("sleep_stop")


    mp.map_standard_action("test", x_sleep)
    pi.bind_EV_KEY("BTN_X", "test")

    pi.run()
    while True:
        pi.maps_to_execute_queue.get().executeAction()



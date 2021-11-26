

class DeviceError(Exception):
    def __init__(self, message='Problem with Device!'):
        super().__init__(message)


class NonExistingPathError(DeviceError):
    def __init__(self, message='Can\'t find any device under given path'):
        super().__init__(message)


class WrongDeviceError(DeviceError):
    def __init__(self, message='There is differently named device under given event!'):
        super().__init__(message)


class DeviceNotPluggedError(DeviceError):
    def __init__(self, message='Device can\'t be found under any path!'):
        super().__init__(message)


class NonExistingInputError(DeviceError):
    def __init__(self, message='Button/joystick/etc. under given name doesn\'t exist in this device!'):
        super().__init__(message)


class ActionError(DeviceError):
    def __init__(self, message='Nothing mapped to this key!'):
        super().__init__(message)


class NoDevicesAddedError(DeviceError):
    def __init__(self, message='There are no added devices with given conditions'):
        super().__init__(message)


class PlaceholderException(Exception):
    def __init__(self, message='Something went terribly wrong if you are seeing this message!'):
        super().__init__(message)
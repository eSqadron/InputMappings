# Input-mappings
Overcomplicated library allowing for quick creations of maps function -> multiple input events.

## Basic usage

First, create an instance of <code>MappingClass</code> object. It's purpose is to assigns names to functions:

```
mp = MappingClass()
mp.map_standard_action("test", lambda: print('test'))
```

Then, create instance of the device that is supposed to generate input, and map the key to previously named function:

```
pad = x360Pad(mp)
pad.map_key("BTN_X", "test")
```

TODO - "generic" devices, like generic pad or generic keyboard
TODO - create list of all devices and names of certain inputs




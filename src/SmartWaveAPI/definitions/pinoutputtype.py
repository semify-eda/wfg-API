from enum import Enum


class PinOutputType(Enum):
    """The output type of a pin."""
    Disable = 0x00
    PushPull = 0x01
    OpenDrain = 0x02

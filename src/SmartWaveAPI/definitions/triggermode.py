from enum import Enum


class TriggerMode(Enum):
    """Specifies the behavior of the trigger on the device."""
    Single = 0x00
    Full = 0x01
    Toggle = 0x02

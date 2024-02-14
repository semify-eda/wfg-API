from enum import Enum


class Command(Enum):
    """The first byte of a command frame to be sent to the device; specifies the meaning of the following bytes."""
    Reset = 0x00
    Trigger = 0x01
    Stop = 0x02
    Stimulus = 0x03
    Driver = 0x04
    Pin = 0x05
    StimulusDriverMatrix = 0x06
    DriverPinMatrix = 0x07
    General = 0x08
    Info = 0x09
    Heartbeat = 0x0A
    FirmwareUpdate = 0x0B
    FpgaUpdate = 0x0C
    FpgaWrite = 0x0D
    FpgaRead = 0x0E

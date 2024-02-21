from enum import Enum


class Statusbit(Enum):
    """The first byte of a status frame sent by the device; specifies the meaning of the following bytes"""
    Idle = 0x01
    Running = 0x02
    Error = 0x03
    Info = 0x04
    Debug = 0x05
    FirmwareUpdateOk = 0x06
    FirmwareUpdateFailed = 0x07
    Readback = 0x08
    SingleAddressRead = 0x09
    PinsStatus = 0x0A
    FirmwareUpdateStatus = 0x0B


class ErrorCode(Enum):
    """Specifies the type of error that occurred."""
    FirmwareCorrupt = 0x00
    FPGACorrupt = 0x01

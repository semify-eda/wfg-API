from typing import List, Union


class I2CWrite(object):
    """A write operation on an I2C driver"""
    def __init__(self, deviceId: int, data: bytes):
        """Create an I2C write operation.

        :param int deviceId: The device ID to write to
        :param bytes data: The data to write to the device"""
        self.deviceId = deviceId
        self.data = data


class I2CRead(object):
    """A read operation on an I2C driver"""
    def __init__(self, deviceId: int, length: int):
        """Create an I2C read operation.

        :param int deviceId: The device ID to read from
        :param int length: The number of bytes to read from the device"""
        self.deviceId = deviceId
        self.length = length


I2CTransaction = Union[I2CWrite, I2CRead]
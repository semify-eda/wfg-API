from typing import Union


class I2CWrite(object):
    """A write operation on an I2C driver"""
    def __init__(self, device_id: int, data: bytes):
        """Create an I2C write operation.

        :param int device_id: The device ID to write to
        :param bytes data: The data to write to the device"""
        self.deviceId = device_id
        self.data = data


class I2CRead(object):
    """A read operation on an I2C driver"""
    def __init__(self, device_id: int, length: int):
        """Create an I2C read operation.

        :param int device_id: The device ID to read from
        :param int length: The number of bytes to read from the device"""
        self.deviceId = device_id
        self.length = length


I2CTransaction = Union[I2CWrite, I2CRead]

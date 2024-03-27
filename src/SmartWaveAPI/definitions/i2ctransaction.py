from typing import Union, List


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

class I2CTransactionResult(object):
    """The result of an I2C transaction"""
    def __init__(self, read: bool, device_id: int, ack_device_id: bool, data: bytes, acks_data: List[bool]):
        """Create an I2C transaction result.

        :param bool read: Whether the transaction was a Read or a Write
        :param int device_id: The device ID that was communicated with
        :param bool ack_device_id: Whether the device sent an ACK in response to the device ID
        :param bytes data: The data that was transferred
        :param bool acks_data: The list of acks received for each data byte """
        self.read: bool = read
        self.device_id: int = device_id
        self.ack_device_id: bool = ack_device_id
        self.data: bytes = data
        self.acks_data: List[bool] = acks_data

I2CTransaction = Union[I2CWrite, I2CRead]

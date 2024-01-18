from typing import List, Union

class I2CWrite(object):
    def __init__(self, deviceId: int, data: List[int]):
        self.deviceId = deviceId
        self.data = data

class I2CRead(object):
    def __init__(self, deviceId: int, length: int):
        self.deviceId = deviceId
        self.length = length

I2CTransaction = Union[I2CWrite, I2CRead]
from typing import List

class I2CTransaction(object):
    def __init__(self, deviceId: int, read: bool, data: List[int]):
        self.deviceId = deviceId
        self.read = read
        self.data = data
from typing import Literal

from SmartWaveAPI.definitions import Command

class Pin:

    def __init__(self, device, bank: Literal['A', 'B'], number: int):
        self._device = device
        self._bank: Literal['A', 'B'] = bank
        self._number: int = number
        self.pullup: bool = False

    def id(self) -> int:
        return ((ord(self._bank[0]) - ord("A") + 0xa) << 4) + self._number

    def writeToDevice(self):
        self._device.writeToDevice(bytes([
            Command.Pin.value,
            self.id(),
            1, # pin input enabled by default
            1 if self.pullup else 0
        ]))

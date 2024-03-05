from typing import Literal, Optional, Callable

from SmartWaveAPI.definitions import Command


class Pin:
    """A hardware pin on the SmartWave device"""

    def __init__(self, device, bank: Literal['A', 'B'], number: int):
        """Create a new pin instance. Only to be called in SmartWave.__init__() function.

        :param SmartWave device: The SmartWave device this pin belongs to
        :param Literal['A', 'B'] bank: The bank this pin belongs to
        :param int number: The number of this pin"""
        self._device = device
        self._bank: Literal['A', 'B'] = bank
        self._number: int = number
        self.pullup: bool = False

        self._inputLevel: Literal[0, 1] = 0
        self.inputLevelCallback: Optional[Callable[[Literal[0, 1]], None]] = None

    def __del__(self):
        """Destructor - return all resources to the device."""
        self.delete()

    def __str__(self):
        """String representation of a pin."""
        return self._bank + str(self._number)

    def id(self) -> int:
        """Calculate the numerical ID of this pin."""
        return ((ord(self._bank[0]) - ord("A") + 0xa) << 4) + self._number

    def writeToDevice(self):
        """Write the configuration parameters of this pin to the device."""
        self._device.writeToDevice(bytes([
            Command.Pin.value,
            self.id(),
            1,  # pin input enabled by default
            1 if self.pullup else 0
        ]))

    def getBank(self) -> str:
        """Get the bank this pin belongs to

        :return: The bank this pin belongs to
        :rtype: str"""
        return self._bank

    def getNumber(self) -> int:
        """Get the number of this pin

        :return: The number of this pin
        :rtype: int"""
        return self._number

    def delete(self):
        """Unconfigure this pin and return its resources to the device."""
        self._device.returnPin(self)

    @property
    def inputLevel(self) -> Literal[0, 1]:
        """Get the current input level of the pin.

        :return: The current input level.
        :rtype: Literal[0, 1]"""
        return self._inputLevel

    @inputLevel.setter
    def inputLevel(self, value: Literal[0, 1]):
        """Set the current input level of the pin - only to be called from SmartWave class.

        :param Literal[0, 1] value: the current input level."""
        if value != self._inputLevel:
            self._inputLevel = value
            if self.inputLevelCallback:
                self.inputLevelCallback(self._inputLevel)

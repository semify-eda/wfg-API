from SmartWaveAPI.definitions import Command, DriverType
from SmartWaveAPI.configitems import Pin

from typing import Dict

class Driver:
    """A hardware driver for a communication protocol"""
    driverType: DriverType = None
    color: str = None

    def __init__(self, device, id: int):
        """Create a new driver instance. Only to be called in the SmartWave.__init__() function.

        :param SmartWave device: The SmartWave device this driver belongs to
        :param int id: The ID of this driver"""
        self._id: int = id
        self._device = device
        self.pins: Dict[str, Pin or None] = {}
        pass

    def __del__(self) -> None:
        """Destructor - return all resources to the device."""
        self.delete()

    def writeToDevice(self):
        """Write the configuration parameters of this driver to the device."""
        raise NotImplementedError

    def writePinConnectionsToDevice(self):
        """Write the pin configuration (i.e. which pin does what) of this driver to the device."""
        for pin in self.pins.keys():
            if self.pins[pin]:
                self._device.writeToDevice(bytes([
                    Command.DriverPinMatrix.value,
                    self.driverType.value,
                    self._id,
                    self.pinNumbers[pin],
                    self.pins[pin].id(),
                    (self.colorRGB565() >> 8) & 0xff,
                    self.colorRGB565() & 0xff,
                    len(pin),
                ]) + bytes(pin, 'ASCII'))

    def removePinConnection(self, pinName: str):
        """Remove the pin connection from the device.

        :param str pinName: The name of the pin to remove"""
        pin = self.pins[pinName]
        if pin is not None and self._device.isConnected():
            self._device.writeToDevice(bytes([
                Command.DriverPinMatrix.value,
                DriverType.NoDriver.value,
                0,  # driver id
                0,  # driver pin id
                pin.id(),
                0xff,  # color l
                0xff,  # color h
                0  # name len
            ]))

    def writePinsToDevice(self):
        """Write the configuration of each of this driver's pins to the device."""
        raise NotImplementedError

    def colorRGB565(self) -> int:
        """Convert this driver's color to an RGB565 value.

        :return: this driver's color as an RGB565 value
        :rtype: int"""
        r = int(self.color[1:3], 16)
        g = int(self.color[3:5], 16)
        b = int(self.color[5:7], 16)

        return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)

    def getId(self) -> int:
        """Get the ID of this driver.

        :return: the ID of this driver
        :rtype: int"""
        return self._id

    def delete(self):
        """Delete this driver along with its pins and return all resources to the device."""
        raise NotImplementedError
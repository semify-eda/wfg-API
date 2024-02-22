from SmartWaveAPI.definitions import Command, DriverType
from SmartWaveAPI.configitems import Pin

from typing import Dict

from src.SmartWaveAPI.definitions import colorRGB565


class Driver:
    """A hardware driver for a communication protocol"""
    driverType: DriverType = None
    color: str = None

    def __init__(self, device, driver_id: int):
        """Create a new driver instance. Only to be called in the SmartWave.__init__() function.

        :param SmartWave device: The SmartWave device this driver belongs to
        :param int driver_id: The ID of this driver"""
        self._id: int = driver_id
        self._device = device
        self.pins: Dict[str, Pin or None] = {}
        self.pinNumbers: Dict[str, int] = {}

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
                    (colorRGB565(self.color) >> 8) & 0xff,
                    colorRGB565(self.color) & 0xff,
                    len(pin),
                ]) + bytes(pin, 'ASCII'))

    def removePinConnection(self, pin_name: str):
        """Remove the pin connection from the device.

        :param str pin_name: The name of the pin to remove"""
        pin = self.pins[pin_name]
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

    def getId(self) -> int:
        """Get the ID of this driver.

        :return: the ID of this driver
        :rtype: int"""
        return self._id

    def delete(self):
        """Delete this driver along with its pins and return all resources to the device."""
        raise NotImplementedError

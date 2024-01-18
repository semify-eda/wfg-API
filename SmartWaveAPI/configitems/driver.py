from SmartWaveAPI.definitions.drivertype import DriverType

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
        pass

    def writeToDevice(self):
        """Write the configuration parameters of this driver to the device."""
        raise NotImplementedError

    def writePinConnectionsToDevice(self):
        """Write the pin configuration (i.e. which pin does what) of this driver to the device."""
        raise NotImplementedError

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
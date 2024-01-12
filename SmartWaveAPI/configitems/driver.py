from SmartWaveAPI.definitions.drivertype import DriverType

class Driver:
    driverType: DriverType = None
    color: str = None

    def __init__(self, device, id: int):
        self._id: int = id
        self._device = device
        pass

    def writeToDevice(self):
        raise NotImplementedError

    def writePinConnectionsToDevice(self):
        raise NotImplementedError

    def colorRGB565(self) -> int:
        r = int(self.color[1:3], 16)
        g = int(self.color[3:5], 16)
        b = int(self.color[5:7], 16)

        return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)
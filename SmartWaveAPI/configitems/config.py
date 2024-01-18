from SmartWaveAPI.definitions import Command
from SmartWaveAPI.configitems import Driver, Stimulus


class Config:
    """A collection of data, driver and pins used to send data via a protocol using the SmartWave."""
    _id_counter: int = 0

    def __init__(self, device, driver: Driver, stimulus: Stimulus):
        """Create a new Config object.

        :param SmartWave device: The SmartWave device this config belongs to
        :param Driver driver: The driver this config uses
        :param Stimulus stimulus: The stimulus this config uses"""
        self._device = device
        self._id: int = Config._id_counter
        Config._id_counter += 1

        self._driver: Driver = driver
        self._stimulus: Stimulus = stimulus

    def writeStimulusDriverConnectionToDevice(self):
        """Configure the connection between the stimulus and the driver on the device."""
        self._device.writeToDevice(bytes([
            Command.StimulusDriverMatrix.value,
            self._stimulus.stimulusType,
            self._id,
            self._driver.driverType.value,
            self._driver._id,
        ]))

    def writeToDevice(self):
        """Write the configurations of all relevant objects to the device."""
        self._driver.writeToDevice()
        self._stimulus.writeToDevice()
        self._driver.writePinConnectionsToDevice()
        self._driver.writePinsToDevice()
        self.writeStimulusDriverConnectionToDevice()

    def getRecorderId(self) -> int:
        """Get the ID of the recorder associated with this Config object.

        :return: The recorder ID
        :rtype: int"""
        return self._stimulus.getId()

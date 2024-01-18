from SmartWaveAPI.definitions import Command
from SmartWaveAPI.configitems import Driver, Stimulus


class Config:
    _id_counter: int = 0

    def __init__(self, device, driver: Driver, stimulus: Stimulus):
        self._device = device
        self._id: int = Config._id_counter
        Config._id_counter += 1

        self._driver: Driver = driver
        self._stimulus: Stimulus = stimulus

    def writeStimulusDriverConnectionToDevice(self):
        self._device.writeToDevice(bytes([
            Command.StimulusDriverMatrix.value,
            self._stimulus.stimulusType,
            self._id,
            self._driver.driverType.value,
            self._driver._id,
        ]))

    def writeToDevice(self):
        self._driver.writeToDevice()
        self._stimulus.writeToDevice()
        self._driver.writePinConnectionsToDevice()
        self._driver.writePinsToDevice()
        self.writeStimulusDriverConnectionToDevice()

    def getRecorderId(self):
        return self._stimulus.getId()

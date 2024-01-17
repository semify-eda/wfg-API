from SmartWaveAPI.configitems import Config, I2CDriver
from SmartWaveAPI.definitions import I2CTransaction

from typing import List


class I2CConfig(Config):
    def __init__(self, device):
        self._device = device
        self._driver: I2CDriver

        driver = self._device.getNextAvailableI2CDriver()

        driver.pins['SCL'] = device.getNextAvailablePin()
        driver.pins['SCL'].pullup = True

        driver.pins['SDA'] = device.getNextAvailablePin()
        driver.pins['SDA'].pullup = True

        stimulus = device.getNextAvailableStimulus()

        stimulus.sampleBitWidth = 32

        super().__init__(self._device, driver, stimulus)
        self.writeToDevice()

    def setTransactions(self, transactions: List[I2CTransaction]):
        self._stimulus.samples = self._driver.generateSamples(transactions)
        self._stimulus.writeToDevice()

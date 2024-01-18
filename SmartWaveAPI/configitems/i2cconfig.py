import threading

from SmartWaveAPI.configitems import Config, I2CDriver, Pin
from SmartWaveAPI.definitions import I2CTransaction, I2CWrite, I2CRead

from typing import List, Union


class I2CConfig(Config):
    def __init__(self, device, sdaPin: Union[Pin, None] = None, sclPin: Union[Pin, None] = None, clockSpeed: Union[int, None] = None):
        self._device = device
        self._driver: I2CDriver

        self._readSemaphore = threading.Semaphore(0)
        self._latestReadValues: List[int] = []

        driver = self._device.getNextAvailableI2CDriver()
        if clockSpeed is not None:
            driver.clockSpeed = clockSpeed

        driver.pins['SCL'] = sdaPin if sdaPin is not None else device.getNextAvailablePin()
        driver.pins['SCL'].pullup = True

        driver.pins['SDA'] = sclPin if sclPin is not None else device.getNextAvailablePin()
        driver.pins['SDA'].pullup = True

        stimulus = device.getNextAvailableStimulus()

        stimulus.sampleBitWidth = 32

        super().__init__(self._device, driver, stimulus)
        self.writeToDevice()

    def setTransactions(self, transactions: List[I2CTransaction]):
        self._stimulus.samples = self._driver.generateSamples(transactions)
        self._stimulus.writeToDevice()

    def write(self, deviceId: int, bytes: List[int]):
        self.setTransactions([
            I2CWrite(deviceId, bytes)
        ])
        self._device.trigger()

    def writeRegister(self, deviceId: int, address: List[int], value: List[int]):
        self.write(deviceId, address + value)

    def _readCallback(self, recorderId: int, values: List[int]):
        if recorderId == self.getRecorderId():
            self._latestReadValues = values
            self._readSemaphore.release()

    def read(self, deviceId: int, length: int, blocking: bool = True) -> Union[None, List[int]]:
        if blocking:
            if self._device.readbackCallback is not None:
                raise Exception("Cannot configure a blocking read operation because there is already a readback "
                                "callback registered on the device")

            # acquire callback
            self._device.readbackCallback = self._readCallback


        self.setTransactions([
            I2CRead(deviceId, length)
        ])
        self._device.trigger()

        if blocking:
            # wait for readback
            self._readSemaphore.acquire()

            # release callback
            self._device.readbackCallback = None

            return self._latestReadValues

        return None

    def readRegister(self, deviceId: int, address: List[int], length: int, blocking: bool = True) -> Union[None, List[int]]:
        if blocking:
            if self._device.readbackCallback is not None:
                raise Exception("Cannot configure a blocking read operation because there is already a readback "
                                "callback registered on the device")

            # acquire callback
            self._device.readbackCallback = self._readCallback


        self.setTransactions([
            I2CWrite(deviceId, address),
            I2CRead(deviceId, length)
        ])
        self._device.trigger()

        if blocking:
            # wait for readback
            self._readSemaphore.acquire()

            # release callback
            self._device.readbackCallback = None

            return self._latestReadValues

        return None

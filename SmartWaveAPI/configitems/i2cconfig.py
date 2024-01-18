import threading

from SmartWaveAPI.configitems import Config, I2CDriver, Pin
from SmartWaveAPI.definitions import I2CTransaction, I2CWrite, I2CRead

from typing import List, Union


class I2CConfig(Config):
    """A collection of data, driver and pins used to send data via I2C using the SmartWave."""
    def __init__(self, device, sdaPin: Union[Pin, None] = None, sclPin: Union[Pin, None] = None, clockSpeed: Union[int, None] = None):
        """Create a new I2C Config object and write the configuration to the connected device.

        :param SmartWave device: The SmartWave device this config belongs to
        :param Union[Pin, None] sdaPin: The pin to use for SDA
        :param Union[Pin, None] sclPin: The pin to use for SCL
        :param int clockSpeed: The transmission clock speed in Hz"""
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
        """Set the list of transactions and send the configuration to the connected device.

        :param List[I2CTransaction] transactions: The list of trasactions"""
        self._stimulus.samples = self._driver.generateSamples(transactions)
        self._stimulus.writeToDevice()

    def write(self, deviceId: int, bytes: List[int]):
        """Write bytes over I2C with the connected device.

        :param int deviceId: The I2C device ID to write to
        :param List[int] bytes: The bytes to write to the I2C bus"""
        self.setTransactions([
            I2CWrite(deviceId, bytes)
        ])
        self._device.trigger()

    def writeRegister(self, deviceId: int, address: List[int], value: List[int]):
        """Write to a register on an I2C device.

        :param int deviceId: The I2C device ID to write to
        :param List[int] address: The address bytes of the target I2C register
        :param List[int] value: The value bytes of the target I2C register"""
        self.write(deviceId, address + value)

    def _readCallback(self, recorderId: int, values: List[int]):
        """Handle the result of an I2C read."""
        if recorderId == self.getRecorderId():
            self._latestReadValues = values
            self._readSemaphore.release()

    def read(self, deviceId: int, length: int, blocking: bool = True) -> Union[None, List[int]]:
        """Read bytes from an I2C device.

        :param int deviceId: The I2C device ID to read from
        :param int length: The number of bytes to read
        :param bool blocking: If true, wait for the response from the connected device
        :return: If blocking == True, return the bytes that were read over I2C. Else return None.
        :rtype: Union[List[int], None]
        :raises Exception: If the blocking mode is requested and another callback for a readback operation is already registered"""
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
        """Read bytes from an I2C device at a specified address.

        :param int deviceId: The I2C device ID to read from
        :param List[int] address: The address bytes where to read from on the I2C device
        :param int length: The number of bytes to read
        :param bool blocking: If true, wait for the response from the connected device
        :return: If blocking == True, return the bytes that were read over I2C. Else return None.
        :rtype: Union[List[int], None]
        :raises Exception: If the blocking mode is requested and another callback for a readback operation is already registered"""
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

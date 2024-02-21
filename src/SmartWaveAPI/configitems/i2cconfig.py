import threading

from SmartWaveAPI.configitems import Config, I2CDriver, Pin
from SmartWaveAPI.definitions import I2CTransaction, I2CWrite, I2CRead

from typing import List, Union


class I2CConfig(Config):
    """A collection of data, driver and pins used to send data via I2C using the SmartWave."""
    def __init__(self,
                 device,
                 sda_pin: Union[Pin, None] = None,
                 scl_pin: Union[Pin, None] = None,
                 clock_speed: Union[int, None] = None):
        """Create a new I2C Config object and write the configuration to the connected device.

        :param SmartWave device: The SmartWave device this config belongs to
        :param Union[Pin, None] sda_pin: The pin to use for SDA
        :param Union[Pin, None] scl_pin: The pin to use for SCL
        :param int clock_speed: The transmission clock speed in Hz"""
        self._device = device

        self._readSemaphore = threading.Semaphore(0)
        self._latestReadValues: bytes = bytes()

        self._driver: I2CDriver = self._device.getNextAvailableI2CDriver()
        self._driver.configure(clock_speed=clock_speed)

        self._driver.pins['SCL'] = sda_pin if sda_pin is not None else device.getNextAvailablePin()
        self._driver.pins['SCL'].pullup = True

        self._driver.pins['SDA'] = scl_pin if scl_pin is not None else device.getNextAvailablePin()
        self._driver.pins['SDA'].pullup = True

        stimulus = device.getNextAvailableStimulus()

        stimulus.sampleBitWidth = 32

        self._lastTransactions: List[I2CTransaction] = []

        super().__init__(self._device, self._driver, stimulus)

        if self._device.isConnected():
            self.writeToDevice()

    def setTransactions(self, transactions: List[I2CTransaction]):
        """Set the list of transactions and send the configuration to the connected device.

        Also checks if the transactions were already the same, and skips reconfiguring the device if so.

        :param List[I2CTransaction] transactions: The list of transactions"""
        changedTransactions = True
        if len(transactions) == len(self._lastTransactions):
            changedTransactions = False
            for newTransaction, oldTransaction in zip(transactions, self._lastTransactions):
                if newTransaction.__dict__ != oldTransaction.__dict__:
                    changedTransactions = True
                    break

        if changedTransactions:
            # write new transactions
            self._lastTransactions = transactions
            self._stimulus.samples = self._driver.generateSamples(transactions)
            self._stimulus.writeToDevice()

            # write new expected read number
            self.writeStimulusDriverConnectionToDevice()

    def write(self, device_id: int, data: bytes):
        """Write bytes over I2C with the connected device.

        If the same write transaction already exists on the device,
        the reconfiguration of the device is skipped.

        :param int device_id: The I2C device ID to write to
        :param bytes data: The bytes to write to the I2C bus"""
        self.setTransactions([
            I2CWrite(device_id, data)
        ])
        self._device.trigger()

    def writeRegister(self, device_id: int, address: bytes, value: bytes):
        """Write to a register on an I2C device.

        If the same write transaction already exists on the device,
        the reconfiguration of the device is skipped.

        :param int device_id: The I2C device ID to write to
        :param bytes address: The address bytes of the target I2C register
        :param bytes value: The value bytes of the target I2C register"""
        self.write(device_id, address + value)

    def _readCallback(self, recorder_id: int, values: List[int]):
        """Handle the result of an I2C read."""
        if recorder_id == self.getRecorderId():
            self._latestReadValues = bytes(values)
            self._readSemaphore.release()

    def read(self, device_id: int, length: int, blocking: bool = True) -> Union[None, bytes]:
        """Read bytes from an I2C device.

        If the same read transaction already exists on the device,
        the reconfiguration of the device is skipped.

        :param int device_id: The I2C device ID to read from
        :param int length: The number of bytes to read
        :param bool blocking: If true, wait for the response from the connected device
        :return: If blocking == True, return the bytes that were read over I2C. Else return None.
        :rtype: Union[bytes, None]
        :raises Exception: If the blocking mode is requested and another callback
        for a readback operation is already registered"""
        if blocking:
            if self._device.readbackCallback is not None:
                raise Exception("Cannot configure a blocking read operation because there is already a readback "
                                "callback registered on the device")

            # acquire callback
            self._device.readbackCallback = self._readCallback

        self.setTransactions([
            I2CRead(device_id, length)
        ])
        self._device.trigger()

        if blocking:
            # wait for readback
            self._readSemaphore.acquire()

            # release callback
            self._device.readbackCallback = None

            return self._latestReadValues

        return None

    def readRegister(self, device_id: int, address: bytes, length: int, blocking: bool = True) -> Union[None, bytes]:
        """Read bytes from an I2C device at a specified address.

        If the same register transaction already exists on the device,
        the reconfiguration of the device is skipped.

        :param int device_id: The I2C device ID to read from
        :param bytes address: The address bytes where to read from on the I2C device
        :param int length: The number of bytes to read
        :param bool blocking: If true, wait for the response from the connected device
        :return: If blocking == True, return the bytes that were read over I2C. Else return None.
        :rtype: Union[List[int], None]
        :raises Exception: If the blocking mode is requested and another callback
        for a readback operation is already registered"""
        if blocking:
            if self._device.readbackCallback is not None:
                raise Exception("Cannot configure a blocking read operation because there is already a readback "
                                "callback registered on the device")

            # acquire callback
            self._device.readbackCallback = self._readCallback

        self.setTransactions([
            I2CWrite(device_id, address),
            I2CRead(device_id, length)
        ])
        self._device.trigger()

        if blocking:
            # wait for readback
            self._readSemaphore.acquire()

            # release callback
            self._device.readbackCallback = None

            return self._latestReadValues

        return None

    def _getReadNumber(self) -> int:
        """Get the number of samples to read back from the device.

        :return: The number of samples
        :rtype: int"""
        readNumber = 0

        for transaction in self._lastTransactions:
            if type(transaction) is I2CRead:
                readNumber += transaction.length

        return readNumber

    @property
    def clockSpeed(self) -> int:
        """The driver's transmission clock speed in Hz"""
        return self._driver.clockSpeed

    @clockSpeed.setter
    def clockSpeed(self, value: int):
        """Set the driver's transmission clock speed in Hz

        :param int value: The transmission clock speed in Hz
        :raises AttributeError: If clockSpeed is not available on the device"""
        self._driver.clockSpeed = value

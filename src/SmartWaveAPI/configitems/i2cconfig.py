import math
import threading

from SmartWaveAPI.configitems import Config, I2CDriver, Pin
from SmartWaveAPI.definitions import I2CTransaction, I2CWrite, I2CRead, I2CTransactionResult

from typing import List, Union, Optional


class I2CConfig(Config):
    """A collection of data, driver and pins used to send data via I2C using the SmartWave."""

    def __init__(self,
                 device,
                 sda_pin: Optional[Pin] = None,
                 scl_pin: Optional[Pin] = None,
                 clock_speed: Optional[int] = None,
                 scl_display_name: Optional[str] = None,
                 sda_display_name: Optional[str] = None):
        """Create a new I2C Config object and write the configuration to the connected device.

        :param SmartWave device: The SmartWave device this config belongs to
        :param Pin sda_pin: The pin to use for SDA. By default, the next unused pin is used.
        :param Pin scl_pin: The pin to use for SCL. By default, the next unused pin is used.
        :param int clock_speed: The transmission clock speed in Hz. Default: 400kHz
        :param str scl_display_name: The name to display for the driver's SCL pin. Default: SCL
        :param str sda_display_name: The name to display for the driver's SDA pin. Default: SDA"""
        self._device = device

        self._readSemaphore = threading.Semaphore(0)
        self._latestReadValues: List[I2CTransactionResult] = []

        self._driver: I2CDriver = self._device.getNextAvailableI2CDriver()
        self._driver.configure(clock_speed=clock_speed, scl_display_name=scl_display_name,
                               sda_display_name=sda_display_name)

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

    def sendTransactions(self,
                         transactions: List[I2CTransaction],
                         blocking: bool = True,
                         timeout: Union[float, None] = 1.0
                         ) -> Union[None, List[I2CTransactionResult]]:
        """Send a transaction over I2C with the connected device.

        If the same transaction already exists on the device,
        the reconfiguration of the device is skipped.

        :param List[I2CTransaction] transactions: The transaction to perform on the bus
        :param bool blocking: If true, wait for the response from the connected device
        :param Union[float, None] timeout: How long to wait for the response from the device in seconds.
            Ignored if blocking is set to False, default 1s, set to None to deactivate timeout.

        :return: If blocking == true, return the information about the transaction on the I2C bus. Else return None.
        :rtype: Union[None, List[I2CTransactionResult]]
        :raises Exception: If the blocking mode is requested and another callback
        for a readback operation is already registered
        :raises TimeoutError: If the timeout for reading back from the device is exceeded."""
        if blocking:
            if self._device.readbackCallback is not None:
                raise Exception("Cannot configure a blocking write operation because there is already a readback "
                                "callback registered on the device")

            # acquire callback
            self._device.readbackCallback = self._readCallback

        self.setTransactions(transactions)
        self._device.trigger()

        if blocking:
            # wait for readback
            if self._readSemaphore.acquire(timeout=timeout):
                # readback successful

                # release callback
                self._device.readbackCallback = None

                return self._latestReadValues
            else:
                # timeout expired
                self._device.readbackCallback = None
                raise TimeoutError("Timeout waiting for readback from device.")

        return None

    def write(self,
              device_id: int,
              data: bytes,
              blocking: bool = True,
              timeout: Union[float, None] = 1.0
              ) -> Union[None, I2CTransactionResult]:
        """Write bytes over I2C with the connected device.

        If the same write transaction already exists on the device,
        the reconfiguration of the device is skipped.

        :param int device_id: The I2C device ID to write to
        :param bytes data: The bytes to write to the I2C bus
        :param bool blocking: If true, wait for the response from the connected device
        :param Union[float, None] timeout: How long to wait for the response from the device in seconds.
            Ignored if blocking is set to False, default 1s, set to None to deactivate timeout.

        :return: If blocking == true, return the information on the transaction on the I2C bus. Else return None.
        :rtype: Union[None, I2CTransactionResult]
        :raises Exception: If the blocking mode is requested and another callback
        for a readback operation is already registered
        :raises TimeoutError: If the timeout for reading back from the device is exceeded."""
        transactions = [I2CWrite(device_id, data)]
        ret = self.sendTransactions(transactions, blocking, timeout)

        if ret is not None and len(ret):
            return ret[0]
        else:
            return ret

    def writeRegister(self,
                      device_id: int,
                      address: bytes,
                      value: bytes,
                      blocking: bool = True,
                      timeout: Union[float, None] = 1.0):
        """Write to a register on an I2C device.

        If the same write transaction already exists on the device,
        the reconfiguration of the device is skipped.

        :param int device_id: The I2C device ID to write to
        :param bytes address: The address bytes of the target I2C register
        :param bytes value: The value bytes of the target I2C register
        :param bool blocking: If true, wait for the response from the connected device
        :param Union[float, None] timeout: How long to wait for the response from the device in seconds.
            Ignored if blocking is set to False, default 1s, set to None to deactivate timeout.

        :return: If blocking == true, return the information on the transaction on the I2C bus. Else return None.
        :rtype: Union[bytes, I2CTransactionResult]
        :raises Exception: If the blocking mode is requested and another callback
        for a readback operation is already registered
        :raises TimeoutError: If the timeout for reading back from the device is exceeded."""
        return self.write(device_id, address + value, blocking, timeout)

    def _readCallback(self, recorder_id: int, values: List[int]):
        """Handle the result of an I2C read."""
        if recorder_id == self.getRecorderId():
            self._latestReadValues = []
            while len(values):
                info = values.pop(0)

                datalen = info & (0xff)
                device_id = (info >> 8) & 0x7f
                read = True if info & (1 << 16) else False
                ack_device_id = True if info & (1 << 17) else False

                data = []
                data_acks = []
                for i in range(math.ceil(datalen / 2.0)):
                    if len(values) == 0:
                        break
                    dataframe = values.pop(0)

                    # first
                    data.append(dataframe & 0xff)
                    data_acks.append(True if dataframe & (1 << 8) else False)

                    # second
                    if (dataframe & (1 << 25)):
                        data.append(dataframe >> 16 & 0xff)
                        data_acks.append(True if dataframe & (1 << 24) else False)

                self._latestReadValues.append(I2CTransactionResult(
                    read=read,
                    device_id=device_id,
                    ack_device_id=ack_device_id,
                    data=bytes(data),
                    acks_data=data_acks
                ))

            self._readSemaphore.release()

    def read(self,
             device_id: int,
             length: int,
             blocking: bool = True,
             timeout: Union[float, None] = 1.0
             ) -> Union[None, I2CTransactionResult]:
        """Read bytes from an I2C device.

        If the same read transaction already exists on the device,
        the reconfiguration of the device is skipped.

        :param int device_id: The I2C device ID to read from
        :param int length: The number of bytes to read
        :param bool blocking: If true, wait for the response from the connected device
        :param Union[float, None] timeout: How long to wait for the response from the device in seconds.
            Ignored if blocking is set to False, default 1s, set to None to deactivate timeout.

        :return: If blocking == True, return the information on the transaction on the I2C bus. Else return None.
        :rtype: Union[None, I2CTransactionResult]
        :raises Exception: If the blocking mode is requested and another callback
        for a readback operation is already registered
        :raises TimeoutError: If the timeout for reading back from the device is exceeded."""

        transactions = [I2CRead(device_id, length)]
        ret = self.sendTransactions(transactions, blocking, timeout)

        if ret is not None and len(ret):
            return ret[0]
        else:
            return ret


    def readRegister(self,
                     device_id: int,
                     address: bytes,
                     length: int,
                     blocking: bool = True,
                     timeout: Union[float, None] = 1.0) -> Union[None, List[I2CTransactionResult]]:
        """Read bytes from an I2C device at a specified address.

        If the same register transaction already exists on the device,
        the reconfiguration of the device is skipped.

        :param int device_id: The I2C device ID to read from
        :param bytes address: The address bytes where to read from on the I2C device
        :param int length: The number of bytes to read
        :param bool blocking: If true, wait for the response from the connected device
        :rtype: Union[List[int], None]
        :param Union[float, None] timeout: How long to wait for the response from the device in seconds.
            Ignored if blocking is set to False, default 1s, set to None to deactivate timeout.

        :return: If blocking == True, return the information on the transaction on the I2C bus. Else return None.
        :rtype: Union[None, I2CTransactionResult]
        :raises Exception: If the blocking mode is requested and another callback
        for a readback operation is already registered
        :raises TimeoutError: If the timeout for reading back from the device is exceeded."""

        transactions = [
            I2CWrite(device_id, address),
            I2CRead(device_id, length)
        ]

        return self.sendTransactions(transactions, blocking, timeout)

    def _getReadNumber(self) -> int:
        """Get the number of samples to read back from the device.

        :return: The number of samples
        :rtype: int"""
        readNumber = 0

        for transaction in self._lastTransactions:
            readNumber += 1  # info word
            datalength = len(transaction.data) if type(transaction) is I2CWrite else transaction.length
            readNumber += math.ceil(datalength / 2.0)

        return readNumber

    def scanAdresses(self,
                     range_lower: int = 0,
                     range_upper: int = 0x7f,
                     timeout: Union[float, None] = 5.0) -> List[int]:
        """Scan a given range of addresses on the I2C Bus and return the list of connected device IDs.
        
        :param int range_lower: The address at which to start searching
        :param int range_upper: The address at which to stop searching
        :param Union[float, None] timeout: How long to wait for the response from the device in seconds.
            Default 5s, set to None to deactivate timeout.
        
        :returns: A list of connected device IDs
        :rtype: List[int]
        :raises ValueError If the range is not within [0x00, 0x7f] or range_lower is bigger than range_upper
        :raises Exception: If another callback for a readback operation is already registered"""
        if range_lower > range_upper:
            raise ValueError("range_lower cannot be bigger than range_upper")
        if range_lower < 0:
            raise ValueError("range_lower cannot be smaller than 0")
        if range_upper > 0x7f:
            raise ValueError("range_upper cannot be bigger than 0x7f")

        transactions = [
            I2CRead(x, 1)
            for x in range(range_lower, range_upper + 1)
        ]

        results = self.sendTransactions(transactions, timeout=timeout)

        device_ids = []
        for result in results:
            if (result.ack_device_id):
                device_ids.append(result.device_id)

        return device_ids



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

    @property
    def sclDisplayName(self) -> str:
        """The name to display for the driver's SCL pin"""
        return self._driver.sclDisplayName

    @sclDisplayName.setter
    def sclDisplayName(self, value: str) -> None:
        """Set the name to display for the driver's SCL pin.

        :param str value: The name to display for the driver's SCL pin."""
        self._driver.sclDisplayName = value

    @property
    def sdaDisplayName(self) -> str:
        """The name to display for the driver's SDA pin"""
        return self._driver.sdaDisplayName

    @sdaDisplayName.setter
    def sdaDisplayName(self, value: str) -> None:
        """Set the name to display for the SDA pin.

        :param str value: The name to display for the driver's SDA pin."""
        self._driver.sdaDisplayName = value

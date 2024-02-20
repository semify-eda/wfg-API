from typing import Union
from SmartWaveAPI.configitems import Pin, Config, SPIDriver, Literal, List
import threading


class SPIConfig(Config):
    """A collection of data, driver and pins used to send data via SPI using the SmartWave."""
    def __init__(self,
                 device,
                 sclkPin: Union[Pin, None] = None,
                 mosiPin: Union[Pin, None] = None,
                 misoPin: Union[Pin, None] = None,
                 ssPin: Union[Pin, None] = None,
                 clockspeed: Union[int, None] = None,
                 bitWidth:  Union[int, None] = None,
                 bitNumbering: Union[Literal["MSB", "LSB"], None] = None,
                 cspol: Union[Literal[0, 1], None] = None,
                 cpol: Union[Literal[0, 1], None] = None,
                 cphase: Union[Literal[0, 1], None] = None):
        """Create a new SPI Config object and write the configuration to the connected device.

        :param SmartWave device: The SmartWave device this config belongs to
        :param Union[Pin, None] sclkPin: The pin to use for SCLK
        :param Union[Pin, None] mosiPin: The pin to use for MOSI
        :param Union[Pin, None] misoPin: The pin to use for MISO
        :param Union[Pin, None] ssPin: The pin to use for SS
        :param int clockspeed: The transmission clock speed in Hz
        :param int bitWidth: The bit width of the SPI transmissions
        :param Literal["MSB", "LSB"] bitNumbering: Whether to transmit MSB-first or LSB-first
        :param Literal[0, 1] cspol: The polarity of the chipselect pin
        :param Literal[0, 1] cpol: The polarity of the clock pin
        :param Literal[0, 1] cphase: The phase of the clock"""
        self._device = device

        self._readSemaphore = threading.Semaphore(0)
        self._latestReadValues: List[int] = []

        self._driver: SPIDriver = self._device.getNextAvailableSPIDriver()
        self._driver.configure(
            clockSpeed=clockspeed,
            bitWidth=bitWidth,
            bitNumbering=bitNumbering,
            cspol=cspol,
            cpol=cpol,
            cphase=cphase
        )

        self._driver.pins['SCLK'] = sclkPin if sclkPin is not None else device.getNextAvailablePin()
        self._driver.pins['MOSI'] = mosiPin if mosiPin is not None else device.getNextAvailablePin()
        self._driver.pins['MISO'] = misoPin if misoPin is not None else device.getNextAvailablePin()
        self._driver.pins['SS'] = ssPin if ssPin is not None else device.getNextAvailablePin()

        stimulus = device.getNextAvailableStimulus()
        stimulus.sampleBitWidth = 32

        self._lastData: List[int] = []

        super().__init__(self._device, self._driver, stimulus)

        # TODO update SPIDriver to write to device itself and remove this
        if self._device.isConnected():
            self.writeToDevice()

    def setData(self, data: List[int]):
        """Set the data and send the configuration to the connected device.

         Also checks if the data is new, and skips reconfiguring the device if not.

        :param List[int] data: The data to send"""
        changedData = True
        if len(data) == len(self._lastData):
            changedData = False
            for newDatum, oldDatum in zip(data, self._lastData):
                if newDatum != oldDatum:
                    changedData = True
                    break

        if changedData:
            # write new transactions
            self._lastData = data
            self._stimulus.samples = data
            self._stimulus.writeToDevice()

            # write new expected read number
            self.writeStimulusDriverConnectionToDevice()

    def _readCallback(self, recorderId: int, values: List[int]):
        """Handle the result of an SPI read."""
        if recorderId == self.getRecorderId():
            self._latestReadValues = values
            self._readSemaphore.release()

    def write(self, data: List[int], blockingRead: bool = True) -> Union[None, List[int]]:
        """Write data over SPI with the connected device.

        If the data is not new, the reconfiguration of the device is skipped.

        :param List[int] data: The data to write
        :param bool blockingRead: If true, wait for the response from the connected device
        :return: If blockingRead == True, return the values that were read over SPI. Else return None.
        :rtype: Union[None, List[int]]
        :raises Exception: If the blocking read mode is requested and another callback for a
            readback operation is already registered."""

        if blockingRead:
            if self._device.readbackCallback is not None:
                raise Exception("Cannot configure a blocking read operation because there is already "
                                "a readback callback registered on the device")

            # acquire callback
            self._device.readbackCallback = self._readCallback

        self.setData(data)
        self._device.trigger()

        if blockingRead:
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
        return len(self._lastData)

    @property
    def clockSpeed(self) -> int:
        """The transmission clock speed in Hz."""
        return self._driver.clockSpeed

    @clockSpeed.setter
    def clockSpeed(self, value: int):
        """Set the transmisison clock speed in Hz.

        :param int value: The transmission clock speed in Hz
        :raises AttributeError: if clockSpeed is not available on the device"""
        self._driver.clockSpeed = value

    @property
    def bitWidth(self) -> int:
        """The bit width of the SPI transmissions"""
        return self._driver.bitWidth

    @bitWidth.setter
    def bitWidth(self, value: int):
        """Set the bit width of the SPI transmissions

        :param int value: The bit width of the SPI transmissions
        :raises AttributeError: If bitWidth is not between 1 and 32"""
        self._driver.bitWidth = value

    @property
    def bitNumbering(self) -> Literal["MSB", "LSB"]:
        """The bit numbering of the SPI transmissions; MSB-first or LSB-first"""
        return self._driver.bitNumbering

    @bitNumbering.setter
    def bitNumbering(self, value: Literal["MSB", "LSB"]):
        """Set the bit numbering of the SPI transmissions; MSB-first or LSB-first

        :param Literal["MSB", "LSB"] value: The bit numbering of the SPI transmissions"""
        self._driver.bitNumbering = value

    @property
    def cspol(self) -> Literal[0, 1]:
        """The polarity of the chipselect pin"""
        return self._driver.cspol

    @cspol.setter
    def cspol(self, value: Literal[0, 1]):
        """Set the polarity of the chipselect pin

        :param Literal[0, 1] value: The polarity of the chipselect pin"""
        self._driver.cspol = value

    @property
    def cpol(self) -> Literal[0, 1]:
        """The polarity of the clock pin"""
        return self._driver.cpol

    @cpol.setter
    def cpol(self, value: Literal[0, 1]):
        """Set the polarity of the clock pin

        :param Literal[0, 1] value: The polarity of the clock pin"""
        self._driver.cpol = value

    @property
    def cphase(self) -> Literal[0, 1]:
        """The phase of the clock pin"""
        return self._driver.cphase

    @cphase.setter
    def cphase(self, value: Literal[0, 1]):
        """Set the polarity of the clock pin

        :param Literal[0, 1] value: The polarity of the clock pin"""
        self._driver.cphase = value

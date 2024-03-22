from typing import Union
from SmartWaveAPI.configitems import Pin, Config, SPIDriver, Literal, List, Optional
import threading


class SPIConfig(Config):
    """A collection of data, driver and pins used to send data via SPI using the SmartWave."""
    def __init__(self,
                 device,
                 sclk_pin: Optional[Pin] = None,
                 mosi_pin: Optional[Pin] = None,
                 miso_pin: Optional[Pin] = None,
                 cs_pin: Optional[Pin] = None,
                 clockspeed: Optional[int] = None,
                 bit_width:  Optional[int] = None,
                 bit_numbering: Optional[Literal["MSB", "LSB"]] = None,
                 cspol: Optional[Literal[0, 1]] = None,
                 cpol: Optional[Literal[0, 1]] = None,
                 cphase: Optional[Literal[0, 1]] = None,
                 sclk_display_name: Optional[str] = None,
                 mosi_display_name: Optional[str] = None,
                 miso_display_name: Optional[str] = None,
                 cs_display_name: Optional[str] = None):
        """Create a new SPI Config object and write the configuration to the connected device.

        :param SmartWave device: The SmartWave device this config belongs to
        :param Optional[Pin] sclk_pin: The pin to use for SCLK. By default, the next unused pin is used.
        :param Optional[Pin] mosi_pin: The pin to use for MOSI. By default, the next unused pin is used.
        :param Optional[Pin] miso_pin: The pin to use for MISO. By default, the next unused pin is used.
        :param Optional[Pin] cs_pin: The pin to use for CS. By default, the next unused pin is used.
        :param int clockspeed: The transmission clock speed in Hz
        :param int bit_width: The bit width of the SPI transmissions
        :param Literal["MSB", "LSB"] bit_numbering: Whether to transmit MSB-first or LSB-first
        :param Literal[0, 1] cspol: The polarity of the chipselect pin
        :param Literal[0, 1] cpol: The polarity of the clock pin
        :param Literal[0, 1] cphase: The phase of the clock
        :param str sclk_display_name: The name to display for the driver's SCLK pin. Default: SCLK
        :param str mosi_display_name: The name to display for the driver's MOSI pin. Default: MOSI
        :param str miso_display_name: The name to display for the driver's MISO pin. Default: MISO
        :param str cs_display_name: The name to display for the driver's CS pin. Default: CS"""
        self._device = device

        self._readSemaphore = threading.Semaphore(0)
        self._latestReadValues: List[int] = []

        self._driver: SPIDriver = self._device.getNextAvailableSPIDriver()
        self._driver.configure(
            clockSpeed=clockspeed,
            bitWidth=bit_width,
            bitNumbering=bit_numbering,
            cspol=cspol,
            cpol=cpol,
            cphase=cphase,
            sclk_display_name=sclk_display_name,
            mosi_display_name=mosi_display_name,
            miso_display_name=miso_display_name,
            cs_display_name=cs_display_name
        )

        self._driver.pins['SCLK'] = sclk_pin if sclk_pin is not None else device.getNextAvailablePin()
        self._driver.pins['MOSI'] = mosi_pin if mosi_pin is not None else device.getNextAvailablePin()
        self._driver.pins['MISO'] = miso_pin if miso_pin is not None else device.getNextAvailablePin()
        self._driver.pins['CS'] = cs_pin if cs_pin is not None else device.getNextAvailablePin()

        stimulus = device.getNextAvailableStimulus()
        stimulus.sampleBitWidth = 32

        self._lastData: List[int] = []

        super().__init__(self._device, self._driver, stimulus)

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

    def _readCallback(self, recorder_id: int, values: List[int]):
        """Handle the result of an SPI read."""
        if recorder_id == self.getRecorderId():
            self._latestReadValues = values
            self._readSemaphore.release()

    def write(self,
              data: List[int],
              blocking_read: bool = True,
              timeout: Union[float, None] = 1.0
              ) -> Union[None, List[int]]:
        """Write data over SPI with the connected device.

        If the data is not new, the reconfiguration of the device is skipped.

        :param List[int] data: The data to write
        :param bool blocking_read: If true, wait for the response from the connected device
        :param float timeout: How long to wait for the response from the device in seconds.
            Ignored if blocking_read is set to False, default 1s, set to None to deactivate timeout.

        :return: If blockingRead == True, return the values that were read over SPI. Else return None.
        :rtype: Union[None, List[int]]
        :raises Exception: If the blocking read mode is requested and another callback for a
            readback operation is already registered.
        :raises TimeoutError: If the timeout for reading back from the device is exceeded."""

        if blocking_read:
            if self._device.readbackCallback is not None:
                raise Exception("Cannot configure a blocking read operation because there is already "
                                "a readback callback registered on the device")

            # acquire callback
            self._device.readbackCallback = self._readCallback

        self.setData(data)
        self._device.trigger()

        if blocking_read:
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

    @property
    def sclkDisplayName(self) -> str:
        """The name to display for the driver's SCLK pin."""
        return self._driver.sclkDisplayName

    @sclkDisplayName.setter
    def sclkDisplayName(self, value: str) -> None:
        """Set the name to display for the driver's SCLK pin.

        :param str value: The name to display for the driver's SCLK pin."""
        self._driver.sclkDisplayName = value

    @property
    def misoDisplayName(self) -> str:
        """The name to display for the driver's MISO pin."""
        return self._driver.misoDisplayName

    @misoDisplayName.setter
    def misoDisplayName(self, value: str) -> None:
        """Set the name to display for the driver's MISO pin.

        :param str value: The name to display for the driver's MISO pin."""
        self._driver.misoDisplayName = value

    @property
    def mosiDisplayName(self) -> str:
        """The name to display for the driver's MOSI pin."""
        return self._driver.mosiDisplayName

    @mosiDisplayName.setter
    def mosiDisplayName(self, value: str) -> None:
        """Set the name to display for the driver's MOSI pin.

        :param str value: The name to display for the driver's MOSI pin."""
        self._driver.mosiDisplayName = value

    @property
    def csDisplayName(self) -> str:
        """The name to display for the driver's CS pin."""
        return self._driver.csDisplayName

    @csDisplayName.setter
    def csDisplayName(self, value: str) -> None:
        """Set the name to display for the driver's CS pin.

        :param str value: The name to display for the driver's CS pin."""
        self.csDisplayName = value


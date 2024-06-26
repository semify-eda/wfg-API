from typing import Dict, Literal, Optional

from SmartWaveAPI.configitems import Driver, Pin
from SmartWaveAPI.definitions import DriverType, Command


class SPIDriver(Driver):
    """A hardware SPI driver on the SmartWave device"""
    driverType = DriverType.SPI
    color: str = '#ab5848'

    def __init__(self,
                 device,
                 id: int,
                 clockSpeed: int = 25e6,
                 bitWidth: int = 8,
                 bitNumbering: Literal["MSB", "LSB"] = "MSB",
                 cspol: Literal[0, 1] = 0,
                 cpol: Literal[0, 1] = 0,
                 cphase: Literal[0, 1] = 0,
                 cs_inactive_time: int = 1):
        """Create a new SPI driver instance. Only to be called in SmartWave.__init__() function.

        :param SmartWave device: The SmartWave device this driver belongs to
        :param int id: The ID of this driver
        :param int clockSpeed: The transmission clock speed in Hz
        :param int bitWidth: The bit width of the SPI transmissions
        :param Literal["MSB", "LSB"] bitNumbering: Whether to transmit MSB-first or LSB-first
        :param Literal[0, 1] cspol: The polarity of the chipselect pin
        :param Literal[0, 1] cpol: The polarity of the clock pin
        :param Literal[0, 1] cphase: The phase of the clock
        :param int cs_inactive_time: How long the CS line should send an inactive level between words, in clock cycles. Default: 1

        :raises AttributeError: If clockSpeed is not available on the device
        :raises AttributeError: If bitWidth is not between 1 and 32"""
        super().__init__(device, id)
        self._clockSpeed: int
        self._checkAndSetClockSpeed(clockSpeed)
        self._bitWidth: int
        self._checkAndSetBitWidth(bitWidth)
        self._bitNumbering: Literal["MSB", "LSB"] = bitNumbering
        self._cspol: Literal[0, 1] = cspol
        self._cpol: Literal[0, 1] = cpol
        self._cphase: Literal[0, 1] = cphase
        self._csInactiveTime: int = cs_inactive_time

        self.pins: Dict[str, Pin or None] = {
            "SCLK": None,
            "MOSI": None,
            "MISO": None,
            "CS": None,
        }
        self.pinNumbers: Dict[str, int] = {
            "SCLK": 0,
            "CS": 1,
            "MOSI": 2,
            "MISO": 3,
        }
        self._displayNames: Dict[str, str] = {
            "SCLK": "SCLK",
            "MOSI": "MOSI",
            "MISO": "MISO",
            "CS": "CS",
        }

    def __del__(self) -> None:
        """Destructor - return all resources to the device."""
        self.delete()

    def writeToDevice(self):
        """Write the configuration parameters of this driver to the device."""
        cdiv = int(self._device.FPGAClockSpeed / (self.clockSpeed * 2))

        self._device.writeToDevice(bytes([
            Command.Driver.value,
            self.driverType.value,
            self._id,
            1,  # enable
            self._bitWidth & 0xff,
            1 if self._bitNumbering == "MSB" else 0,
            self._cpol,
            self._cspol,
            self._cphase,
            (cdiv >> 8) & 0xff,
            cdiv & 0xff,
            self._csInactiveTime
        ]))

    def _checkAndSetClockSpeed(self, clockSpeed: int):
        """Check the clock speed for correctness and set the local variable.

        :param int clockSpeed: The clock speed in Hz
        :raises ValueError: If the clock speed is not available on the device"""
        if clockSpeed > self._device.FPGAClockSpeed / 4:
            raise AttributeError("The desired clock speed is too high")
        if clockSpeed < self._device.FPGAClockDivided / 2:
            raise AttributeError("The desired clock speed is too slow")
        self._clockSpeed = clockSpeed

    def _checkAndSetBitWidth(self, bitWidth: int):
        """Check the bitwidth for correctness and set the local variable.

        :param int bitWidth: The bitwidth
        :raises AttributeError: If the bitwidth is not between 1 and 32"""
        if bitWidth < 1:
            raise AttributeError("The desired bitwidth is too small")
        elif bitWidth > 32:
            raise AttributeError("The desired bitwidth is too big")
        self._bitWidth = bitWidth

    def configure(self,
                  clockSpeed: Optional[int] = None,
                  bitWidth: Optional[int] = None,
                  bitNumbering: Optional[Literal["MSB", "LSB"]] = None,
                  cspol: Optional[Literal[0, 1]] = None,
                  cpol: Optional[Literal[0, 1]] = None,
                  cphase: Optional[Literal[0, 1]] = None,
                  sclk_display_name: Optional[str] = None,
                  mosi_display_name: Optional[str] = None,
                  miso_display_name: Optional[str] = None,
                  cs_display_name: Optional[str] = None,
                  cs_inactive_time: Optional[int] = None,
                  ):
        """Configure the settings of this driver and write them to the connected device.

        :param int clockSpeed: The transmission clock speed in Hz
        :param int bitWidth: The bit width of the SPI transmissions
        :param Literal["MSB", "LSB"] bitNumbering: Whether to transmit MSB-first or LSB-first
        :param Literal[0, 1] cspol: The polarity of the chipselect pin
        :param Literal[0, 1] cpol: The polarity of the clock pin
        :param Literal[0, 1] cphase: The phase of the clock
        :param str sclk_display_name: The name to display for the SCLK pin
        :param str mosi_display_name: The name to display for the MOSI pin
        :param str miso_display_name: The name to display for the MISO pin
        :param str cs_display_name: The name to display for the CS pin
        :param int cs_inactive_time: How long the CS line should send an inactive level between words, in clock cycles

        :raises AttributeError: If clockSpeed is not available on the device
        :raises AttributeError: If bitWidth is not between 1 and 32"""

        if clockSpeed is not None:
            self._checkAndSetClockSpeed(clockSpeed)

        if bitWidth is not None:
            self._checkAndSetBitWidth(bitWidth)

        if bitNumbering is not None:
            self._bitNumbering = bitNumbering

        if cspol is not None:
            self._cspol = cspol

        if cpol is not None:
            self._cpol = cpol

        if cphase is not None:
            self._cphase = cphase

        if sclk_display_name is not None:
            self._displayNames["SCLK"] = sclk_display_name

        if mosi_display_name is not None:
            self._displayNames["MOSI"] = mosi_display_name

        if miso_display_name is not None:
            self._displayNames["MISO"] = miso_display_name

        if cs_display_name is not None:
            self._displayNames["CS"] = cs_display_name

        if cs_inactive_time is not None:
            self._csInactiveTime = cs_inactive_time

        if self._device.isConnected():
            self.writeToDevice()
            self.writePinConnectionsToDevice()

    @property
    def clockSpeed(self) -> int:
        """The transmission clock speed in Hz."""
        return self._clockSpeed

    @clockSpeed.setter
    def clockSpeed(self, value: int):
        """Set the transmission clock speed in Hz.

        :param int value: The transmission clock speed in Hz
        :raises AttributeError: If clockSpeed is not available on the device"""
        self.configure(clockSpeed=value)

    @property
    def bitWidth(self) -> int:
        """The bit width of the SPI transmissions"""
        return self._bitWidth

    @bitWidth.setter
    def bitWidth(self, value: int):
        """Set the bit width of the SPI transmissions

        :param int value: The bit width of the SPI transmissions
        :raises AttributeError: If bitWidth is not between 1 and 32"""
        self.configure(bitWidth=value)

    @property
    def bitNumbering(self) -> Literal["MSB", "LSB"]:
        """The bit numbering of the SPI transmissions; MSB-first or LSB-first"""
        return self._bitNumbering

    @bitNumbering.setter
    def bitNumbering(self, value: Literal["MSB", "LSB"]):
        """Set the bit numbering of the SPI transmissions; MSB-first or LSB-first

        :param Literal["MSB", "LSB"] value: The bit numbering of the SPI transmissions"""
        self.configure(bitNumbering=value)

    @property
    def cspol(self) -> Literal[0, 1]:
        """The polarity of the chipselect pin"""
        return self._cspol

    @cspol.setter
    def cspol(self, value: Literal[0, 1]):
        """Set the polarity of the chipselect pin

        :param Literal[0, 1] value: The polarity of the chipselect pin"""
        self.configure(cspol=value)

    @property
    def cpol(self) -> Literal[0, 1]:
        """The polarity of the clock pin"""
        return self._cpol

    @cpol.setter
    def cpol(self, value: Literal[0, 1]):
        """Set the polarity of the clock pin

        :param Literal[0, 1] value: The polarity of the clock pin"""
        self.configure(cpol=value)

    @property
    def cphase(self) -> Literal[0, 1]:
        """The phase of the clock pin"""
        return self._cphase

    @cphase.setter
    def cphase(self, value: Literal[0, 1]):
        """Set the polarity of the clock pin

        :param Literal[0, 1] value: The polarity of the clock pin"""
        self.configure(cphase=value)

    @property
    def sclkDisplayName(self) -> str:
        """The name to display for the SCLK pin."""
        return self._displayNames["SCLK"]

    @sclkDisplayName.setter
    def sclkDisplayName(self, value: str) -> None:
        """Set the name to display for the SCLK pin.

        :param str value: The name to display for the SCLK pin."""
        self.configure(sclk_display_name=value)

    @property
    def misoDisplayName(self) -> str:
        """The name to display for the MISO pin."""
        return self._displayNames["MISO"]

    @misoDisplayName.setter
    def misoDisplayName(self, value: str) -> None:
        """Set the name to display for the MISO pin.

        :param str value: The name to display for the MISO pin."""
        self.configure(miso_display_name=value)

    @property
    def mosiDisplayName(self) -> str:
        """The name to display for the MOSI pin."""
        return self._displayNames["MOSI"]

    @mosiDisplayName.setter
    def mosiDisplayName(self, value: str) -> None:
        """Set the name to display for the MOSI pin.

        :param str value: The name to display for the MOSI pin."""
        self.configure(mosi_display_name=value)

    @property
    def csDisplayName(self) -> str:
        """The name to display for the CS pin."""
        return self._displayNames["CS"]

    @csDisplayName.setter
    def csDisplayName(self, value: str) -> None:
        """Set the name to display for the CS pin.

        :param str value: The name to display for the CS pin."""
        self.configure(cs_display_name=value)

    @property
    def csInactiveTime(self) -> int:
        """How long the CS line is inactive between words, in clock cycles."""
        return self._csInactiveTime

    @csInactiveTime.setter
    def csInactiveTime(self, value: int) -> None:
        """Set the CS inactive time, in clock cycles.

        :param int value: The time in clock cycles how long the CS line should be inactive between words"""
        self.configure(cs_inactive_time=value)


    def writePinsToDevice(self):
        """Write the configuration of each of this driver's pins to the device."""
        for pin in self.pins.keys():
            if self.pins[pin]:
                self.pins[pin].writeToDevice()


    def delete(self):
        """Unconfigure this driver along with its pins and return all resources to the device."""
        for pin in self.pins.keys():
            if self.pins[pin]:
                self.pins[pin].delete()
                self.removePinConnection(pin)
            self.pins[pin] = None

        self._device.returnSPIDriver(self)
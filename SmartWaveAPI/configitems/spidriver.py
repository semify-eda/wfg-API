from typing import Dict, Literal, Union

from SmartWaveAPI.configitems import Driver, Pin
from SmartWaveAPI.definitions import DriverType, Command


class SPIdriver(Driver):
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
                 cphase: Literal[0, 1] = 0):
        """Create a new SPI driver instance. Only to be called in SmartWave.__init__() function.

        :param SmartWave device: The SmartWave device this driver belongs to
        :param int id: The ID of this driver
        :param int clockSpeed: The transmission clock speed in Hz
        :param int bitWidth: The bit width of the SPI transmissions
        :param Literal["MSB", "LSB"] bitNumbering: Whether to transmit MSB-first or LSB-first
        :param Literal[0, 1] cspol: The polarity of the chipselect pin
        :param Literal[0, 1] cpol: The polarity of the clock pin
        :param Literal[0, 1] cphase: The phase of the clock

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

        self.pins: Dict[str, Pin or None] = {
            "SCLK": None,
            "MOSI": None,
            "MISO": None,
            "SS": None,
        }
        self.pinNumbers: Dict[str, int] = {
            "SCLK": 1,
            "MOSI": 2,
            "MISO": 3,
            "SS": 4,
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
            cdiv & 0xff
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
                  clockSpeed: Union[int, None] = None,
                  bitWidth: Union[int, None] = None,
                  bitNumbering: Union[Literal["MSB", "LSB"], None] = None,
                  cspol: Union[Literal[0, 1], None] = None,
                  cpol: Union[Literal[0, 1], None] = None,
                  cphase: Union[Literal[0, 1], None] = None):
        """Configure the settings of this driver and write them to the connected device.

        :param int clockSpeed: The transmission clock speed in Hz
        :param int bitWidth: The bit width of the SPI transmissions
        :param Literal["MSB", "LSB"] bitNumbering: Whether to transmit MSB-first or LSB-first
        :param Literal[0, 1] cspol: The polarity of the chipselect pin
        :param Literal[0, 1] cpol: The polarity of the clock pin
        :param Literal[0, 1] cphase: The phase of the clock

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

        self.writeToDevice()

    @property
    def clockSpeed(self) -> int:
        """The transmission clock speed in Hz"""
        return self._clockSpeed

    @clockSpeed.setter
    def clockSpeed(self, value: int):
        """Set the transmission clock speed in Hz

        :param int value: The transmission clock speed in Hz
        :raises AttributeError: If clockSpeed is not available on the device"""
        self.configure(clockSpeed=value)

    @property
    def bitWidth(self) -> int:
        """The bit widht of the SPI transmissions"""
        return self._bitWidth

    @bitWidth.setter
    def bitWidth(self, value: int):
        """Set the bit width of the SPI transmissions

        :param int bitWidth: The bit width of the SPI transmissions
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


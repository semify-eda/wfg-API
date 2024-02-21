from SmartWaveAPI.configitems import Pin
from SmartWaveAPI.definitions import Command, DriverType, PinOutputType

from typing import Literal, Optional, Callable


class GPIO:
    """A hardware GPIO pin on the SmartWave device."""
    driverType: DriverType = DriverType.GPIO
    color: str = "#435880"

    def __init__(self,
                 device,
                 pin: Pin,
                 name: str = "GPIO",
                 level: Literal[0, 1] = 0,
                 pullup: bool = False,
                 output_type: PinOutputType = PinOutputType.Disable,
                 input_level_callback: Optional[Callable[[Literal[0, 1]], None]] = None):
        """Create a new GPIO instance.

        :param SmartWave device: The SmartWave device this GPIO belongs to
        :param Pin pin: The pin on which to set up IO
        :param str name: The name of the pin, displayed on the device
        :param Literal[0, 1] level: The initial level of the pin
        :param bool pullup: Whether to enable a pullup resistor on the pin
        :param PinOutputType output_type: The output type of the pin
        :param Callable[[Literal[0, 1]], None]: A callable to be run whenever the input level of the pin is changed."""
        self._device = device
        self._pin: Pin = pin

        self._name: str = name
        self._level: Literal[0, 1] = level
        self._output_type: PinOutputType = output_type
        self._pullup: bool = pullup

        self.configure(name, level, pullup, output_type)
        self.inputLevelCallback = input_level_callback

    def __del__(self):
        """Destructor - return all resources to the device."""
        self.delete()

    def __enter__(self):
        """Enter - return instance."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit - delete config"""
        self.delete()

    def configure(self,
                  name: Optional[str] = None,
                  level: Optional[Literal[0, 1]] = None,
                  pullup: Optional[bool] = None,
                  output_type: Optional[PinOutputType] = None):
        """Configure the settings of this GPIO pin and write them to the connected device.

        :param str name: The name of the pin, displayed on the device
        :param Literal[0, 1] level: The initial level of the pin
        :param bool pullup: Whether to enable a pullup resistor on the pin
        :param PinOutputType output_type: The output type of the pin"""
        if name is not None:
            self._name = name

        if level is not None:
            self._level = level

        if pullup is not None:
            self._pin.pullup = pullup
            self._pin.writeToDevice()

        if output_type is not None:
            self._outputType = output_type

        self._pin.writeToDevice()
        self._device.writeToDevice(bytes([
            Command.DriverPinMatrix.value,
            DriverType.GPIO.value,
            self._outputType.value,
            self._level,
            self._pin.id(),
            (self.colorRGB565() >> 8) & 0xff,
            self.colorRGB565() & 0xff,
            len(self._name)
        ]) + bytes(self._name, 'ASCII'))

    def colorRGB565(self) -> int:
        """Convert this driver's color to an RGB565 value.

        :return: this driver's color as an RGB565 value
        :rtype: int"""
        r = int(self.color[1:3], 16)
        g = int(self.color[3:5], 16)
        b = int(self.color[5:7], 16)

        return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)

    def delete(self):
        """Delete this GPIO pin and return all resources to the device."""
        self._pin.delete()

    @property
    def name(self) -> str:
        """The name of the pin.

        :return: The name of the pin.
        :rtype: str"""
        return self._name

    @name.setter
    def name(self, name: str):
        """Set the name of the pin.

        :param str name: The name of the pin"""
        self.configure(name=name)

    @property
    def level(self) -> Literal[0, 1]:
        """The output level of the pin.

        :return: The output level of the pin.
        :rtype: Literal[0, 1]"""
        return self._level

    @level.setter
    def level(self, level: Literal[0, 1]):
        """Set the output level of the pin.

        :param Literal[0, 1] level: The output level of the pin."""
        self.configure(level=level)

    @property
    def pullup(self) -> bool:
        """Whether the pullup is enabled on the pin.

        :return: Whether the pullup is enabled on the pin.
        :rtype: bool"""
        return self._pullup

    @pullup.setter
    def pullup(self, pullup: bool):
        """Set the pullup on the pin

        :param bool pullup: Whether to enable the pullup resistor on the pin"""
        self.configure(pullup=pullup)

    @property
    def outputType(self) -> PinOutputType:
        """The output type of the pin.

        :return: The output type of the pin
        :rtype: PinOutputType"""
        return self._outputType

    @outputType.setter
    def outputType(self, output_type: PinOutputType):
        """Set the output type of the pin.

        :param PinOutputType output_type: The output type of the pin"""
        self.configure(output_type=output_type)

    @property
    def inputLevelCallback(self) -> Optional[Callable[[Literal[0, 1]], None]]:
        """Get the current registered input level callback.

        The input level callback is a function that is called whenever the
        input level on the pin changes.

        :return: Current registered callback
        :rtype: Optional[Callable[[Literal[0, 1]], None]]"""
        return self._pin.inputLevelCallback

    @inputLevelCallback.setter
    def inputLevelCallback(self, input_level_callback: Optional[Callable[[Literal[0, 1]], None]]):
        """Set the input level callback.

        Caution: this overrides any input level callback that was registered on this GPIO, or the connected pin.

        :param Optional[Callable[[Literal[0, 1]], None]] input_level_callback: The input level callback, or None to unset."""
        self._pin.inputLevelCallback = input_level_callback

    @property
    def inputLevel(self) -> Literal[0, 1]:
        """Get the current input level.

        :return: Current input level.
        :rtype: Literal[0, 1]"""
        return self._pin.inputLevel


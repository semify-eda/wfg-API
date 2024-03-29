import math
from typing import Dict, List, Optional
from .pin import Pin

from SmartWaveAPI.configitems import Driver
from SmartWaveAPI.definitions import Command, DriverType, I2CRead, I2CWrite, I2CTransaction


class I2CDriver(Driver):
    """A hardware I2C driver on the SmartWave device."""
    driverType = DriverType.I2C
    color: str = '#a54be2'

    def __init__(self, device, driver_id: int, clock_speed: int = 400e3):
        """Create a new I2C driver instance. Only to be called in SmartWave.__init__() function.

        :param SmartWave device: The SmartWave device this driver belongs to
        :param int driver_id: The ID of this driver
        :param int clock_speed: The transmission clock speed in Hz
        :raises AttributeError: If clockSpeed is not available on the device"""
        super().__init__(device, driver_id)
        self._clockSpeed: int
        self._checkAndSetClockSpeed(clock_speed=clock_speed)
        self.pins: Dict[str, Pin or None] = {
            'SCL': None,
            'SDA': None
        }
        self.pinNumbers: Dict[str, int] = {
            'SCL': 0,
            'SDA': 1
        }
        self._displayNames: Dict[str, str] = {
            "SCL": "SCL",
            "SDA": "SDA"
        }

    def __del__(self) -> None:
        """Destructor - return all resources to the device."""
        self.delete()

    def writeToDevice(self):
        """Write the configuration parameters of this driver to the device."""

        cdiv = int(self._device.FPGAClockSpeed / (self._clockSpeed * 6))

        self._device.writeToDevice(bytes([
            Command.Driver.value,
            self.driverType.value,
            self._id,
            1,  # enable
            (cdiv >> 8) & 0xff,
            cdiv & 0xff
        ]))

    def _checkAndSetClockSpeed(self, clock_speed: int):
        """Check the clock speed for correctness and set the local variable.

        :param int clock_speed: The clock speed in Hz
        :raises ValueError: If the clock speed is not available on the device"""
        if clock_speed > 3e6:
            raise AttributeError("The desired clock speed is too high")
        if clock_speed < self._device.FPGAClockDivided / 2:
            raise AttributeError("The desired clock speed is too low")
        self._clockSpeed = clock_speed

    def configure(self,
                  clock_speed: Optional[int] = None,
                  scl_display_name: Optional[str] = None,
                  sda_display_name: Optional[str] = None):
        """Configure the settings of this driver and write them to the connected device.
        
        :param int clock_speed: The transmission clock speed in Hz
        :param str scl_display_name: The name to display for the SCL pin
        :param str sda_display_name: The name to display for the SDA pin
        :raises AttributeError: If clockSpeed is not available on the device"""
        if clock_speed is not None:
            self._checkAndSetClockSpeed(clock_speed)

        if scl_display_name is not None:
            self._displayNames["SCL"] = scl_display_name

        if sda_display_name is not None:
            self._displayNames["SDA"] = sda_display_name

        if self._device.isConnected():
            self.writeToDevice()
            self.writePinConnectionsToDevice()

    @property
    def clockSpeed(self) -> int:
        """The transmission clock speed in Hz"""
        return self._clockSpeed

    @clockSpeed.setter
    def clockSpeed(self, value: int):
        """Set the transmission clock speed in Hz

        :param int value: The transmission clock speed in Hz
        :raises AttributeError: If clockSpeed is not available on the device"""
        self.configure(clock_speed=value)

    @property
    def sclDisplayName(self) -> str:
        """The name to display for the SCL pin"""
        return self._displayNames["SCL"]

    @sclDisplayName.setter
    def sclDisplayName(self, value: str) -> None:
        """Set the name to display for the SCL pin.

        :param str value: The name to display for the SCL pin."""
        self.configure(scl_display_name=value)

    @property
    def sdaDisplayName(self) -> str:
        """The name to display for the SDA pin"""
        return self._displayNames["SDA"]

    @sdaDisplayName.setter
    def sdaDisplayName(self, value: str) -> None:
        """Set the name to display for the SDA pin.

        :param str value: The name to display for the SDA pin."""
        self.configure(sda_display_name=value)

    def writePinsToDevice(self):
        """Write the configuration of each of this driver's pins to the device."""
        for pin in self.pins.keys():
            if self.pins[pin]:
                self.pins[pin].writeToDevice()

    def generateSamples(self, transactions: List[I2CTransaction]) -> List[int]:
        """Generate a stream of bytes for the SmartWave to interpret as I2C Transactions.

        :param I2CTransaction transactions: List of I2C transactions
        :return: List of samples for the SmartWave to interpret as I2C Transactions
        :rtype: List[int]"""
        samples = []
        for transaction in transactions:
            length = len(transaction.data) if type(transaction) is I2CWrite else transaction.length
            read = type(transaction) is I2CRead

            command_frame = 0
            command_frame |= length & 0xff  # datalength
            command_frame |= (1 if read else 0) << 9  # read/not write
            command_frame |= 1 << 10  # use device select in frame
            command_frame |= (transaction.deviceId & 0xff) << 16  # device Id
            command_frame |= 0xC << 28  # command frame marker

            samples.append(command_frame)

            data_frame = 0
            data_frame |= 0xD << 28  # data frame marker

            num_data_frames = math.ceil(length / 2.0)

            data_frames = [data_frame] * num_data_frames
            for i in range(num_data_frames):
                # first data in frame
                if not read:
                    data_frames[i] |= (transaction.data[i * 2])  # data
                if read:
                    data_frames[i] |= 1 << 8  # ack
                data_frames[i] |= 1 << 9  # valid

                if (i + 1) * 2 <= length:
                    # second data in frame
                    if not read:
                        data_frames[i] |= (transaction.data[i * 2 + 1]) << 16  # data
                    if read:
                        data_frames[i] |= 1 << 24  # ack
                    data_frames[i] |= 1 << 25  # valid

            if num_data_frames == 0:
                data_frames.append(data_frame)

            samples += data_frames

        return samples

    def delete(self):
        """Unconfigure this driver along with its pins and return all resources to the device."""
        if self.pins["SDA"]:
            self.pins["SDA"].delete()
            self.removePinConnection("SDA")

        if self.pins["SCL"]:
            self.pins["SCL"].delete()
            self.removePinConnection("SCL")

        self.pins["SDA"] = None
        self.pins["SCL"] = None

        self._device.returnI2CDriver(self)

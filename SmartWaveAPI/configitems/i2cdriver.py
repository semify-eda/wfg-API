from typing import Dict, List
from .pin import Pin

from SmartWaveAPI.configitems import Driver
from SmartWaveAPI.definitions import Command, DriverType, I2CRead, I2CWrite, I2CTransaction


class I2CDriver(Driver):
    """An hardware I2C driver on the SmartWave device"""
    driverType = DriverType.I2C
    color: str = '#a54be2'

    def __init__(self, device, id: int, clockSpeed: int = 400e3):
        """Create a new I2C driver instance. Only to be called in SmartWave.__init__() function.

        :param SmartWave device: The SmartWave device this driver belongs to
        :param int id: The ID of this driver
        :param int clockSpeed: The transmission clock speed in Hz"""
        super().__init__(device, id)
        self.clockSpeed: int = clockSpeed
        self.pins: Dict[str, Pin or None] = {
            'SCL': None,
            'SDA': None
        }
        self.pinNumbers: Dict[str, int] = {
            'SCL': 0,
            'SDA': 1
        }

    def __del__(self) -> None:
        """Destructor - return all resources to the device."""
        self.delete()

    def writeToDevice(self):
        """Write the configuration parameters of this driver to the device."""

        cdiv = int(self._device.FPGAClockSpeed / (self.clockSpeed * 6))

        self._device.writeToDevice(bytes([
            Command.Driver.value,
            self.driverType.value,
            self._id,
            1,
            (cdiv >> 8) & 0xff,
            cdiv & 0xff
        ]))





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
            command_frame += length & 0xff
            command_frame += 1 << 16  # use device select in frame
            command_frame += (transaction.deviceId & 0xff) << 17
            command_frame |= (1 if read else 0) << 25

            samples.append(command_frame)
            if not read:
                samples += transaction.data

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


from typing import Dict, List
from .pin import Pin

from SmartWaveAPI.configitems import Driver
from SmartWaveAPI.definitions import Command, DriverType, I2CTransaction


class I2CDriver(Driver):
    driverType = DriverType.I2C
    color: str = '#a54be2'

    def __init__(self, device, id: int):
        super().__init__(device, id)
        self.clockSpeed: int = 400e3
        self.pins: Dict[str, Pin or None] = {
            'SCL': None,
            'SDA': None
        }
        self.pinNumbers: Dict[str, int] = {
            'SCL': 0,
            'SDA': 1
        }

    def writeToDevice(self):

        cdiv = int(self._device.FPGAClockSpeed / (self.clockSpeed * 6)) # TODO check clockspeed

        self._device.writeToDevice(bytes([
            Command.Driver.value,
            self.driverType.value,
            self._id,
            1,
            (cdiv >> 8) & 0xff,
            cdiv & 0xff
        ]))


    def writePinConnectionsToDevice(self):
        for pin in self.pins.keys():
            if self.pins[pin]:
                self._device.writeToDevice(bytes([
                    Command.DriverPinMatrix.value,
                    self.driverType.value,
                    self._id,
                    self.pinNumbers[pin],
                    self.pins[pin].id(),
                    (self.colorRGB565() >> 8) & 0xff,
                    self.colorRGB565() & 0xff,
                    len(pin),
                ]) + bytes(pin, 'ASCII'))


    def generateSamples(self, transactions: List[I2CTransaction]) -> List[int]:
        samples = []
        for transaction in transactions:
            command_frame = 0
            command_frame += len(transaction.data) & 0xff
            command_frame += 1 << 16  # use device select in frame
            command_frame += (transaction.deviceId & 0xff) << 17
            command_frame |= (transaction.read & 0x1) << 25

            samples.append(command_frame)
            samples += transaction.data

        return samples
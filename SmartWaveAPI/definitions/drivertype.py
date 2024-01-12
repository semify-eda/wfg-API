from enum import Enum

class DriverType(Enum):
    SPI = 0x00
    I2C = 0x01
    I2S = 0x02
    UART = 0x03

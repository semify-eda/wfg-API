# Description 
A python API for the SmartWave interface.

## Installation
- This package requires python version 3.
- To install this package, run the following command:
```bash
pip install SmartWaveAPI
```

## Usage
It is recommended to use the `with..as` pattern to implicitly call cleanup functions 
when resources of the SmartWave device are no longer needed.
### Basic I2C script
```python
from SmartWaveAPI import SmartWave

with SmartWave().connect() as sw:
    with sw.createI2CConfig() as i2c:
        # write 0xaa, 0x55 to device with address 0x20
        i2c.write(0x20, bytes([0xaa, 0x55]))
        # read 2 bytes from device with address 0x20
        i2c.read(0x20, 2)
        # write value 0x0f to register 0xaa of device at 0x20
        i2c.writeRegister(0x20, 0xaa.to_bytes(1, "big"), 0x0f.to_bytes(1, "big"))
        # read value of 1-byte register 0xaa of device at 0x20
        i2c.readRegister(0x20, 0xaa.to_bytes(1, "big"), 1)
```

### Basic SPI script
```python
from SmartWaveAPI import SmartWave

with SmartWave().connect() as sw:
    with sw.createSPIConfig() as spi:
        # write 0xaa, 0x55 via SPI and read simultaneously
        spi.write([0xaa, 0x55])
```

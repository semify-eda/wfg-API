# SmartWave Python API

`SmartWaveAPI` is the Python interface to the **SmartWave** device. It configures the device's
on-board FPGA protocol engines — I2C, SPI, UART and GPIO — and runs transactions through them over a
USB serial link, so you can drive and observe a target chip from a plain Python script.

## Installation
```bash
pip install SmartWaveAPI
```
Requires Python 3.8 or newer.

## Concepts
- **`SmartWave`** — the device connection. `SmartWave().connect()` finds and opens the board.
- **Driver configs** — `createI2CConfig(...)`, `createSPIConfig(...)`, `createGPIO(...)` set up one of
  the FPGA's protocol engines on the chosen pins and return an object you run transactions on.
- **`with … as`** — the recommended pattern; it frees the device's resources automatically on exit.

## Quickstart (I2C)
```python
from SmartWaveAPI import SmartWave

with SmartWave().connect() as sw:                 # find + open the device
    with sw.createI2CConfig("A1", "A2") as i2c:   # SDA = A1, SCL = A2
        i2c.write(0x20, bytes([0xaa, 0x55]))                       # write two bytes to device 0x20
        data = i2c.read(0x20, 2)                                   # read two bytes back
        i2c.writeRegister(0x20, 0x0a.to_bytes(1, "big"),           # write reg 0x0a = 0x0f
                          0x0f.to_bytes(1, "big"))
        val = i2c.readRegister(0x20, 0x0a.to_bytes(1, "big"), 1)   # read 1-byte reg 0x0a
```
SPI and GPIO follow the same shape via `createSPIConfig(...)` / `createGPIO(...)`.

## API reference
The full class and method documentation is in the module reference (see the navigation):
- **`SmartWaveAPI.smartwave`** — the `SmartWave` connection object
- **`SmartWaveAPI.configitems`** — the driver/config classes (I2C, SPI, GPIO, stimulus, pins)
- **`SmartWaveAPI.definitions`** — enums and data types (commands, transactions, …)

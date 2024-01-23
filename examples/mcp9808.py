"""
Demo script for the MCP9808 Temperature sensor
"""

from SmartWaveAPI import SmartWave
import time


def temp_read():
    """
    This function sets up a connection to SmartWave and the MCP9808 Temperature sensor via I2C
    After that, we read out the content of the ambient temperature register, and convert the data
    into degree Celsius.
    """
    sw = SmartWave()
    sw.connect()

    i2c = sw.createI2CConfig("A1", "A2")
    i2c.write(0x18, [0x07])
    device_id = i2c.readRegister(0x18, [0x07], 1)
    if device_id[0] != 0x4:     # The Device ID for the MCP9808 is 0x04
        raise ValueError("Device ID is incorrect!")
    else:
        print(f"Successfully connected to device ID: {device_id[0]:#0x}")

        i2c.write(0x18, [0x05])
        upper_byte, ta_lsb = i2c.readRegister(0x18, [0x05], 2)
        msb = bin(upper_byte)[2:].zfill(8)
        ta_msb = int(msb[4:])
        sign = int(msb[5])
        if sign == 0:
            t_ambient = (ta_msb * 2 ** 4) + (ta_lsb * 2 ** (-4))
        else:
            t_ambient = 256 - ((ta_msb * 2 ** 4) + (ta_lsb * 2 ** (-4)))
        print(f"Measured Temperature is {t_ambient:.2f}°C")

    time.sleep(1)
    sw.disconnect()


if __name__ == "__main__":
    temp_read()

"""
Demo script for interfacing with the INA260 Power Sensor via I2C
"""

from SmartWaveAPI import SmartWave
import time


def meas_voltage(i2c):
    """
    Read out the content of the Bus Voltage Register (0x02) and convert it into decimal format.
    Display the measured voltage in mV.
    """
    lsb_volt = 1.25e-3
    i2c.write(0x40, [0x02])
    volt_read = i2c.readRegister(0x40, [0x02], 2)
    print(f"Vbus Register content: {bin(int.from_bytes(volt_read, 'big', signed=False))}")
    volt_val = lsb_volt * (int.from_bytes(volt_read, 'big', signed=False))
    print(f"Measured voltage: {volt_val:.2f}V")


def meas_current(i2c):
    """
    Read out the content of the Current Register (0x01) and convert it into decimal format.
    Display the calculate current in mA.
    """
    lsb_current = 1.25e-3
    i2c.write(0x40, [0x01])
    current_read = i2c.readRegister(0x40, [0x01], 2)
    print(f"Current Register content: {bin(int.from_bytes(current_read, 'big', signed=False))}")
    current_val = lsb_current * (int.from_bytes(current_read, 'big', signed=True))
    print(f"Measured current: {current_val:.2f}A")


def meas_power(i2c):
    """
    Read out the content of the Power Register (0x03) and convert it into decimal format.
    Display the calculated power in mW.
    """
    lsb_power = 10e-3
    i2c.write(0x40, [0x03])
    power_read = i2c.readRegister(0x40, [0x03], 2)
    print(f"Power Register content: {bin(int.from_bytes(power_read, 'big', signed=False))}")
    power_val = lsb_power * (int.from_bytes(power_read, 'big', signed=False))
    print(f"Measured power: {power_val:.2f}W")


def main():
    """
    Setup connection to SmartWave and read out the device ID of the INA260 sensor.
    """
    sw = SmartWave()
    sw.connect()

    i2c = sw.createI2CConfig("A1", "A2")
    i2c.write(0x40, [0xff])
    device_id = i2c.readRegister(0x40, [0xff], 2)
    if device_id[0] == 0xff:
        raise ValueError("Couldn't reach device. Terminating code.")
    else:
        print(f"Connection was successful. Device ID: {device_id[0]:#0x}")

    meas_voltage(i2c)
    meas_current(i2c)
    meas_power(i2c)

    time.sleep(1)
    sw.disconnect()


if __name__ == "__main__":
    main()

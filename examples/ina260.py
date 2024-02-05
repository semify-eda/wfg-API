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
    lsb_volt = 1.25
    i2c.write(0x40, [0x02])
    volt_read = i2c.readRegister(0x40, [0x02], 2)
    print(f"Vbus Register content: {bin(volt_read[0] + volt_read[1])[2:].zfill(8)}")
    volt_val = lsb_volt * (volt_read[0] + volt_read[1])
    print(f"Measured voltage: {volt_val:.2f}mV")


def meas_current(i2c):
    """
    Read out the content of the Current Register (0x01) and convert it into decimal format.
    Display the calculate current in mA.
    """
    lsb_current = 1.25
    i2c.write(0x40, [0x01])
    current_read = i2c.readRegister(0x40, [0x01], 2)
    print(f"Current Register content: {bin(current_read[0] + current_read[1])[2:].zfill(8)}")
    current_val = lsb_current * (current_read[0] + current_read[1])
    print(f"Measured current: {current_val:.2f}mA")


def meas_power(i2c):
    """
    Read out the content of the Power Register (0x03) and convert it into decimal format.
    Display the calculated power in mW.
    """
    lsb_power = 10
    i2c.write(0x40, [0x03])
    power_read = i2c.readRegister(0x40, [0x03], 2)
    print(f"Power Register content: {bin(power_read[0] + power_read[1])[2:].zfill(8)}")
    power_val = lsb_power * (power_read[0] + power_read[1])
    print(f"Measured power: {power_val:.2f}mW")


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

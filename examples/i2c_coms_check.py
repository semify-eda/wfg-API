"""
Test script to check I2C communication setup
"""
import numpy as np
import time
from SmartWaveAPI import SmartWave
from SmartWaveAPI.configitems import *
from SmartWaveAPI.definitions import *


def i2c_addr_sweep(i2c):
    """
        Sweep all the possible I2C addresses and wait for the ACK.
    :param i2c: SmartWave I2C object
    :return: device specific I2C address
    """
    i2c_addr = None
    dummy_byte = (0).to_bytes(1, 'big')
    i2c_addr_list = np.arange(0, 127)
    for addr in i2c_addr_list:
        i2c.write(int(i2c_addr_list[addr]), dummy_byte)      # TODO: replace with read/write function to return ACK
        ack = i2c.read(int(i2c_addr_list[addr]), 1)
        if (ack[0] == 0xff) or (ack[0] == 0x00):
            if addr == i2c_addr_list[-1]:
                print("Couldn't reach device.")
            continue
        else:
            i2c_addr = i2c_addr_list[addr]
            print(f"Connection was successful. I2C address is: {i2c_addr:#0x}")
            break

    return i2c_addr


def main():
    """
    Setup I2C communication on SmartWave and perform a complete check:
    - SDA, SCL can be pull-down or pull-up
    - no shorts between SCL and SDA
    - maximal clock frequency
    - send command to target device and check for ACK
    - check for correct target
    :return: none
    """

    with SmartWave().connect() as sw:
        with sw.createI2CConfig("A1", "A2", int(200e3)) as i2c:
            print("Successfully connected to SmartWave")

            # Function for sweeping I2C addresses
            print("Trying to connect to target device")
            i2c_dev_addr = i2c_addr_sweep(i2c)
            if i2c_dev_addr is None:
                print("Reducing clock speed to 100kHz and try to reconnect")
                # Change clock speed from 400kHz -> 100kHz
                # TODO: Add function to reduce the clock speed
                i2c_dev_addr = i2c_addr_sweep(i2c)
                if i2c_dev_addr is None:
                    print("Swap SDA / SCL and retry")
                    retry = input("Press 'R' to retry or 'Q' to quit: ")
                    if retry.upper() == 'R':
                        i2c_dev_addr = i2c_addr_sweep(i2c)
                        if i2c_dev_addr is None:
                            raise ValueError("Couldn't reach device. Terminating code.")
                    else:
                        raise ValueError("Couldn't reach device. Terminating code.")

            print(f"Read target specific register for device ID wit address: {i2c_dev_addr:#0x}")


if __name__ == "__main__":
    main()

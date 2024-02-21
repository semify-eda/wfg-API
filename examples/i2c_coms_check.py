"""
Test script to check I2C communication setup
"""
import sys
import logging
import numpy as np
from datetime import datetime

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
        if ack[0] == 0xff:
            if addr == i2c_addr_list[-1]:
                logging.warning("Couldn't reach device.")
            continue
        else:
            i2c_addr = i2c_addr_list[addr]
            logging.info(f"Connection was successful. I2C address is: {i2c_addr:#0x}")
            break

    return i2c_addr


def read_dev_id(i2c, i2c_addr, reg_pointer):
    """
    Read a user specified register of the target device for identification
    :param i2c:  SmartWave I2C object
    :param i2c_addr: Device Specific I2C address
    :param reg_pointer: User defined register address
    :return: Unique Device ID
    """
    dummy_byte = (0).to_bytes(1, 'big')
    i2c.writeRegister(i2c_addr, reg_pointer, dummy_byte)
    device_id = i2c.readRegister(i2c_addr, reg_pointer, 1)
    logging.info(f"Unique Device ID: {device_id[0]:#0x}")
    return device_id[0]


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
    date_time = datetime.now().strftime("%d.%m.%Y_%H.%M.%S")
    file_name = f'I2C_coms_check_{date_time}.log'
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        encoding='utf-8', level=logging.DEBUG,
                        handlers=[logging.StreamHandler(sys.stdout),
                                  logging.FileHandler(filename=file_name)]
                        )

    scl = 'A1'
    sda = 'A2'
    fast_clk = int(400e3)
    slow_clk = int(100e3)

    with SmartWave().connect() as sw:
        with sw.createI2CConfig(scl, sda, fast_clk) as i2c:
            logging.info("Successfully connected to SmartWave")
            logging.info(f"SCL is set to pin: {scl} | SDA is set to pin: {sda} "
                         f"| I2C clock running at {fast_clk//1e3} kHz")

            # Function for sweeping I2C addresses
            logging.info("Trying to connect to the target device")
            i2c_dev_addr = i2c_addr_sweep(i2c)
            if i2c_dev_addr is None:
                logging.debug("Reducing the I2C clock speed to 100kHz and try to reconnect")
                i2c.clockSpeed = slow_clk
                logging.debug(f"I2C is running at {i2c.clockSpeed // 1e3} kHz")
                i2c_dev_addr = i2c_addr_sweep(i2c)
                if i2c_dev_addr is None:
                    logging.debug("Please swap the SDA / SCL lines and retry")
                    retry = input("Press 'R' to retry or 'Q' to quit: ")
                    if retry.upper() == 'R':
                        i2c_dev_addr = i2c_addr_sweep(i2c)
                        if i2c_dev_addr is None:
                            raise ValueError("Couldn't reach device. Terminating code.")
                    else:
                        raise ValueError("Couldn't reach device. Terminating code.")

            # Function for reading device specific ID
            logging.info(f"Read target specific register for device ID wit address: {i2c_dev_addr:#0x}")
            user_reg = int(input("Please enter the register address in HEX that you want to read: "), base=16)
            reg_pointer = user_reg.to_bytes(1, 'big')
            unique_id = read_dev_id(i2c, i2c_dev_addr, reg_pointer)


if __name__ == "__main__":
    main()

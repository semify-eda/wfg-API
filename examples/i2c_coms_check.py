"""
Test script to check I2C communication setup
"""
import sys
import os
import logging
import time
import argparse
from datetime import datetime
from typing import Union, Optional
import numpy as np

# TODO: Change SmartWaveAPI import when the GPIO config has been added to the python package
from src.SmartWaveAPI import SmartWave
from src.SmartWaveAPI.definitions import PinOutputType


def gpio_high_low(gpio_a, gpio_b) -> None:
    """
    Test if SDA and SCL can be pulled-down or up.

    :param gpio_a: SmartWave GPIO_A object
    :param gpio_b: SmartWave GPIO_B object
    :return: None
    """
    errors = 0
    # Test initial condition
    pin_output_type_a = str(gpio_a.outputType).split('.')[1]
    input_level_a = gpio_a.inputLevel
    pin_output_type_b = str(gpio_b.outputType).split('.')[1]
    input_level_b = gpio_b.inputLevel
    logging.info(f"Initial output level of SCL pin: {input_level_a} with push-pull: {pin_output_type_a}")
    logging.info(f"Initial output level of SDA pin: {input_level_b} with push-pull: {pin_output_type_b}")

    # SCL and SDA pulled down
    logging.info("Set both SCL and SDA in pull-down mode.")
    gpio_a.level = 1
    gpio_a.outputType = PinOutputType.PushPull
    gpio_a.pullup = False
    pin_output_type_a = str(gpio_a.outputType).split('.')[1]
    time.sleep(500e-3)
    input_level_a = gpio_a.inputLevel
    output_level_a = gpio_a.level

    gpio_b.level = 1
    gpio_b.outputType = PinOutputType.PushPull
    gpio_b.pullup = False
    pin_output_type_b = str(gpio_b.outputType).split('.')[1]
    time.sleep(500e-3)
    input_level_b = gpio_b.inputLevel
    output_level_b = gpio_b.level

    logging.info(f"Input level of SCL pin: {input_level_a} with output type: {pin_output_type_a} "
                 f"and pull-up set to: {gpio_a.pullup}")
    logging.info(f"Input level of SDA pin: {input_level_b} with output type: {pin_output_type_b} "
                 f"and pull-up set to: {gpio_b.pullup}")

    if not input_level_a:
        logging.error("The SCL pin couldn't be pulled high")
        errors += 1
    if not input_level_b:
        logging.error("The SDA pin couldn't be pulled high")
        errors += 1

    # SCL and SDA pulled up
    logging.info("Set both SCL and SDA in pull-up mode.")
    gpio_a.level = 0
    pin_output_type_a = str(gpio_a.outputType).split('.')[1]
    gpio_a.pullup = True
    time.sleep(500e-3)
    input_level_a = gpio_a.inputLevel
    output_level_a = gpio_a.level

    gpio_b.level = 0
    pin_output_type_b = str(gpio_b.outputType).split('.')[1]
    gpio_b.pullup = True
    time.sleep(500e-3)
    input_level_b = gpio_b.inputLevel
    output_level_b = gpio_b.level

    logging.info(f"Input level of SCL pin: {input_level_a} with output type: {pin_output_type_a} "
                 f"and pull-up set to: {gpio_a.pullup}")
    logging.info(f"Input level of SDA pin: {input_level_b} with output type: {pin_output_type_b} "
                 f"and pull-up set to: {gpio_b.pullup}")

    if input_level_a:
        logging.error("The SCL pin couldn't be pulled low")
        errors += 1
    if input_level_b:
        logging.error("The SDA pin couldn't be pulled low")
        errors += 1

    if errors > 0:
        raise ValueError("Terminating code.")


def gpio_short(gpio_a, gpio_b) -> None:
    """
    Test if there's a short between the SCL and SDA lines

    :param gpio_a: SmartWave GPIO_A object
    :param gpio_b: SmartWave GPIO_B object
    :return: None
    """
    input_level_a = gpio_a.inputLevel
    input_level_b = gpio_b.inputLevel
    # output_level_a = gpio_a.level
    # output_level_b = gpio_b.level
    logging.info(f"Initial output level of SCL pin: {input_level_a}")
    logging.info(f"Initial output level of SDA pin: {input_level_b}")

    logging.info("Set SCL low and SDA high.")
    gpio_a.level = 0
    gpio_b.level = 1
    time.sleep(500e-3)
    input_level_a = gpio_a.inputLevel
    input_level_b = gpio_b.inputLevel
    # output_level_a = gpio_a.level
    # output_level_b = gpio_b.level
    logging.info(f"Output level of SCL pin: {input_level_a}")
    logging.info(f"Output level of SDA pin: {input_level_b}")

    if input_level_a == input_level_b:
        logging.critical("There is a short between SCL and SDA.")
        raise ValueError("Terminating code.")

    logging.info("Set SCL high and SDA low.")
    gpio_a.level = 1
    gpio_b.level = 0
    time.sleep(500e-3)
    input_level_a = gpio_a.inputLevel
    input_level_b = gpio_b.inputLevel
    # output_level_a = gpio_a.level
    # output_level_b = gpio_b.level
    logging.info(f"Output level of SCL pin: {input_level_a}")
    logging.info(f"Output level of SDA pin: {input_level_b}")

    if input_level_a == input_level_b:
        logging.critical("There is a short between SCL and SDA.")
        raise ValueError("Terminating code.")


def i2c_addr_sweep(i2c) -> Union[None, int]:
    """
    Sweep all the possible I2C addresses and wait for the ACK.

    :param i2c: SmartWave I2C object
    :return: device specific I2C address
    """
    i2c_addr = None
    dummy_byte = (0).to_bytes(1, 'big')
    i2c_addr_list = np.arange(0, 127)
    for addr in i2c_addr_list:
        i2c.write(int(i2c_addr_list[addr]), dummy_byte)  # TODO: replace with read/write function to return ACK
        ack = i2c.read(int(i2c_addr_list[addr]), 1)
        if ack[0] == 0xff:
            if addr == i2c_addr_list[-1]:
                logging.warning("Couldn't reach device.")
            continue
        i2c_addr = i2c_addr_list[addr]
        logging.info(f"Connection was successful. I2C address is: {i2c_addr:#0x}")
        break

    return i2c_addr


def read_dev_id(i2c, i2c_addr: int, reg_pointer: bytes, length: Optional[int] = 1) -> None:
    """
    Read a user specified register of the target device for identification

    :param i2c: SmartWave I2C object
    :param i2c_addr: Device Specific I2C address
    :param reg_pointer: User defined register address
    :param length: Register length as bytes
    :return: None
    """
    dummy_byte = (0).to_bytes(1, 'big')
    i2c.writeRegister(i2c_addr, reg_pointer, dummy_byte)
    device_id = i2c.readRegister(i2c_addr, reg_pointer, length)
    logging.info(f"Unique Device ID: {device_id[0]:#0x}")


def register_r_w(i2c, i2c_addr: int, reg_pointer: bytes, reg_val: bytes, length: Optional[int] = 1) -> None:
    """
    Simple function that performs a register read/write with user defined address and data

    :param i2c:  SmartWave I2C object
    :param i2c_addr: Device Specific I2C address
    :param reg_pointer: User defined register address
    :param reg_val: User defined value to write to register
    :param length: Register length as bytes
    :return: None
    """
    max_shift = (length - 1) * 8
    data_to_write = 0
    for pos in range(length):
        data_to_write |= reg_val[pos] << (max_shift - (pos * 8))

    i2c.writeRegister(i2c_addr, reg_pointer, data_to_write.to_bytes(length, 'big'))
    logging.info(f"Value written: {data_to_write:#0x} to address {reg_pointer[0]:#0x}")

    reg_read_back = i2c.readRegister(i2c_addr, reg_pointer, length)
    data_read_back = 0
    for pos in range(length):
        data_read_back |= reg_read_back[pos] << (max_shift - (pos * 8))
    logging.info(f"Value read back: {data_read_back:#0x} from address {reg_pointer[0]:#0x}")

    if data_to_write != data_read_back:
        logging.error("The value read back from the register does not match the written value")
        raise ValueError("Terminating code.")


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

    # Command line arguments provided by the user
    parser = argparse.ArgumentParser(description="Access Registers.")
    parser.add_argument("-scl", "--scl_pin", type=str, help="Select the desired SCL Pin", default='A1')
    parser.add_argument("-sda", "--sda_pin", type=str, help="Select the desired SDA Pin", default='A2')
    parser.add_argument("-id", "--unique_id", type=str, help="Register address of unique device ID in HEX format.")
    parser.add_argument("-rp", "--reg_pointer", type=str, help="Register address to write to in HEX format.")
    parser.add_argument("-rv", "--reg_value", type=str, help="Register value to write in HEX format.")
    args = parser.parse_args()

    directory = "./i2c_check_logs"
    if not os.path.exists(directory):
        os.mkdir(directory)

    date_time = datetime.now().strftime("%Y.%m.%d_%H.%M.%S")
    file_name = f'I2C_coms_check_{date_time}.log'
    fq_fn = os.path.join(directory, file_name)
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                        datefmt="%Y-%m-%d %H:%M:%S",
                        encoding='utf-8', level=logging.DEBUG,
                        handlers=[logging.StreamHandler(sys.stdout),
                                  logging.FileHandler(filename=fq_fn)]
                        )

    scl = args.scl_pin
    sda = args.sda_pin
    fast_clk = int(400e3)
    slow_clk = int(100e3)

    with SmartWave().connect() as sw:
        logging.info("Successfully connected to SmartWave")
        with sw.createGPIO(pin_name=scl, name="SCL") as gpio_A:
            with sw.createGPIO(pin_name=sda, name="SDA") as gpio_B:
                logging.info(f"Create a GPIO instance on target pins {scl} and {sda}")
                logging.info("Test if SCL and SDA can be pulled-down and pulled-up.")
                gpio_high_low(gpio_A, gpio_B)
                logging.info("Check for shorts between SCL and SDA")
                gpio_short(gpio_A, gpio_B)

        with sw.createI2CConfig(scl, sda, fast_clk) as i2c:
            logging.info(f"SCL is set to pin: {scl} | SDA is set to pin: {sda} "
                         f"| I2C clock running at {fast_clk // 1e3} kHz")
            logging.info("Trying to connect to the target device")
            i2c_dev_addr = i2c_addr_sweep(i2c)
            if i2c_dev_addr is None:
                logging.debug("Reducing the I2C clock speed to 100kHz and try to reconnect")
                i2c.clockSpeed = slow_clk
                logging.debug(f"I2C is running at {i2c.clockSpeed // 1e3} kHz")
                i2c_dev_addr = i2c_addr_sweep(i2c)
                if i2c_dev_addr is None:
                    logging.debug("Please swap the SDA / SCL lines and retry")  # TODO: Automate (?)
                    retry = input("Press 'R' to retry or 'Q' to quit: ")
                    if retry.upper() == 'R':
                        i2c_dev_addr = i2c_addr_sweep(i2c)
                        if i2c_dev_addr is None:
                            logging.error("Couldn't reach device. Terminating code.")
                            raise ValueError("Terminating code.")
                    else:
                        logging.error("Couldn't reach device. Terminating code.")
                        raise ValueError("Terminating code.")

            if args.unique_id:
                logging.info(f"Read target specific register for device ID with address: {i2c_dev_addr:#0x}")
                unique_id = bytes.fromhex(args.unique_id)
                read_dev_id(i2c, i2c_dev_addr, unique_id)

            if args.reg_pointer:
                logging.info("Perform a register write / read operation on target device.")
                reg_pointer = bytes.fromhex(args.reg_pointer)
                reg_value = bytes.fromhex(args.reg_value)
                register_r_w(i2c, i2c_dev_addr, reg_pointer, reg_value, length=len(reg_value))

            logging.info(f"I2C checklist was successfully completed. "
                         f"The log files can be found at {os.path.abspath(directory)}")


if __name__ == "__main__":
    main()

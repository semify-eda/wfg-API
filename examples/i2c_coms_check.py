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

from SmartWaveAPI import SmartWave
from SmartWaveAPI.definitions import PinOutputType


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
    pin_output_type_b = str(gpio_b.outputType).split('.')[1]
    input_level_a = gpio_a.inputLevel
    input_level_b = gpio_b.inputLevel
    logging.info(f"Initial output level of SCL pin: {input_level_a} with output type: {pin_output_type_a}")
    logging.info(f"Initial output level of SDA pin: {input_level_b} with output type: {pin_output_type_b}")

    # SCL and SDA pulled down
    logging.info("Set both SCL and SDA in pull-down mode.")
    gpio_a.outputType = PinOutputType.PushPull
    pin_output_type_a = str(gpio_a.outputType).split('.')[1]
    gpio_b.outputType = PinOutputType.PushPull
    pin_output_type_b = str(gpio_b.outputType).split('.')[1]
    gpio_a.pullup = False
    gpio_b.pullup = False
    gpio_a.level = 0
    gpio_b.level = 0
    time.sleep(500e-3)
    input_level_a = gpio_a.inputLevel
    input_level_b = gpio_b.inputLevel

    logging.info(f"Input level of SCL pin: {input_level_a} with output type: {pin_output_type_a} "
                 f"and pull-up set to: {gpio_a.pullup}")
    logging.info(f"Input level of SDA pin: {input_level_b} with output type: {pin_output_type_b} "
                 f"and pull-up set to: {gpio_b.pullup}")

    if input_level_a:
        logging.error("The SCL pin couldn't be pulled high")
        errors += 1
    if input_level_b:
        logging.error("The SDA pin couldn't be pulled high")
        errors += 1

    # SCL and SDA pulled up
    logging.info("Set both SCL and SDA in pull-up mode.")
    gpio_a.outputType = PinOutputType.PushPull
    pin_output_type_a = str(gpio_a.outputType).split('.')[1]
    gpio_b.outputType = PinOutputType.PushPull
    pin_output_type_b = str(gpio_b.outputType).split('.')[1]
    gpio_a.pullup = True
    gpio_b.pullup = True
    gpio_a.level = 1
    gpio_b.level = 1
    time.sleep(500e-3)
    input_level_a = gpio_a.inputLevel
    input_level_b = gpio_b.inputLevel

    logging.info(f"Input level of SCL pin: {input_level_a} with output type: {pin_output_type_a} "
                 f"and pull-up set to: {gpio_a.pullup}")
    logging.info(f"Input level of SDA pin: {input_level_b} with output type: {pin_output_type_b} "
                 f"and pull-up set to: {gpio_b.pullup}")

    if not input_level_a:
        logging.error("The SCL pin couldn't be pulled low")
        errors += 1
    if not input_level_b:
        logging.error("The SDA pin couldn't be pulled low")
        errors += 1

    if errors > 0:
        raise ConnectionError("Terminating code.")


def gpio_short(gpio_a, gpio_b) -> None:
    """
    Test if there's a short between the SCL and SDA lines

    :param gpio_a: SmartWave GPIO_A object
    :param gpio_b: SmartWave GPIO_B object
    :return: None
    """
    # TODO: Due to HW limitations, currently we can only check if a pin is shorted to GND or logic 0

    gpio_a.outputType = PinOutputType.OpenDrain
    gpio_b.outputType = PinOutputType.OpenDrain
    input_level_a = gpio_a.inputLevel
    input_level_b = gpio_b.inputLevel
    logging.info(f"Initial output level of SCL pin: {input_level_a}")
    logging.info(f"Initial output level of SDA pin: {input_level_b}")

    logging.info("Set SCL low and SDA high.")
    gpio_a.level = 0
    gpio_b.level = 1
    time.sleep(500e-3)
    input_level_a = gpio_a.inputLevel
    input_level_b = gpio_b.inputLevel
    logging.info(f"Output level of SCL pin: {input_level_a}")
    logging.info(f"Output level of SDA pin: {input_level_b}")

    if input_level_a == input_level_b:
        logging.critical("There is a short between SCL and SDA.")
        raise ConnectionError("Terminating code.")

    logging.info("Set SCL high and SDA low.")
    gpio_a.level = 1
    gpio_b.level = 0
    time.sleep(500e-3)
    input_level_a = gpio_a.inputLevel
    input_level_b = gpio_b.inputLevel
    logging.info(f"Output level of SCL pin: {input_level_a}")
    logging.info(f"Output level of SDA pin: {input_level_b}")

    if input_level_a == input_level_b:
        logging.critical("There is a short between SCL and SDA.")
        raise ConnectionError("Terminating code.")


def i2c_addr_sweep(i2c, addr_lower: int, addr_upper: int) -> Union[None, int]:
    """
    Sweep all the possible I2C addresses and wait for the ACK.

    :param i2c: SmartWave I2C object
    :param addr_lower: Lower value for the I2C address sweep
    :param addr_upper: Upper value for the I2C address sweep
    :return: device specific I2C address
    """

    logging.info(f"Trying to find the I2C address of the device within the range of {addr_lower} and {addr_upper}")
    if addr_lower < 0:
        logging.warning("Minimum value for the lower range can't be a negative number!")
        raise ValueError("Terminating code.")

    if addr_upper > 127:
        logging.warning("Maximum value for the upper range can't be greater then 127!")
        raise ValueError("Terminating code.")

    i2c_addr = None
    dummy_byte = (0).to_bytes(1, 'big')
    i2c_addr_list = np.arange(addr_lower, addr_upper + 1)
    for addr in range(len(i2c_addr_list)):
        i2c.write(int(i2c_addr_list[addr]), dummy_byte)  # TODO: replace with read/write function to return ACK
        ack = i2c.read(int(i2c_addr_list[addr]), 1)
        if ack is None:
            logging.warning("No device is connected to SmartWave.")
            logging.warning("Check if all the wires are properly connected.")
            raise ConnectionError
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
    dummy_byte = (0).to_bytes(length, 'big')
    i2c.writeRegister(i2c_addr, reg_pointer, dummy_byte)
    device_id = i2c.readRegister(i2c_addr, reg_pointer, length)
    logging.info(f"Unique Device ID: {device_id[0]:#0x}")


def register_r_w(i2c, i2c_addr: int, reg_pointer: bytes, reg_val: bytes,
                 addr_length: Optional[int] = 1, data_length: Optional[int] = 1) -> None:
    """
    Simple function that performs a register read/write with user defined address and data

    :param i2c:  SmartWave I2C object
    :param i2c_addr: Device Specific I2C address
    :param reg_pointer: User defined register address
    :param reg_val: User defined value to write to register
    :param addr_length: Register address length as bytes
    :param data_length: Register data length as bytes
    :return: None
    """

    if (addr_length != 1) and (len(reg_pointer) > 1):
        max_shift = (addr_length - 1) * 8
        addr_to_write = 0
        for pos in range(addr_length):
            addr_to_write |= reg_pointer[pos] << (max_shift - (pos * 8))
    elif (addr_length != 1) and (len(reg_pointer) == 1):
        addr_to_write = []
        reg_point = int.from_bytes(reg_pointer)
        for _ in range(addr_length):
            addr_to_write.append(reg_point)
        addr_to_write = int.from_bytes(bytes(addr_to_write))
    else:
        addr_to_write = int.from_bytes(reg_pointer)

    if (data_length != 1) and (len(reg_val) > 1):
        max_shift = (data_length - 1) * 8
        data_to_write = 0
        for pos in range(data_length):
            data_to_write |= reg_val[pos] << (max_shift - (pos * 8))
    elif (data_length != 1) and (len(reg_val) == 1):
        data_to_write = []
        reg_value = int.from_bytes(reg_val)
        for _ in range(data_length):
            data_to_write.append(reg_value)
        data_to_write = int.from_bytes(bytes(data_to_write))
    else:
        data_to_write = int.from_bytes(reg_val)

    # Register write
    i2c.writeRegister(i2c_addr, addr_to_write.to_bytes(addr_length, 'big'), data_to_write.to_bytes(data_length, 'big'))
    logging.info(f"Value written: {data_to_write:#0x} to address {reg_pointer[0]:#0x}")

    # Register read
    reg_read_back = i2c.readRegister(i2c_addr, addr_to_write.to_bytes(addr_length, 'big'), data_length)
    data_read_back = 0
    max_shift = (data_length - 1) * 8
    for pos in range(data_length):
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

    parser.add_argument("-lower", "--addr_lower", type=int, help="Select the desired SCL Pin", default=0)
    parser.add_argument("-upper", "--addr_upper", type=int, help="Select the desired SDA Pin", default=127)

    parser.add_argument("-id", "--unique_id", type=str, help="Register address of unique device ID in HEX format.")

    parser.add_argument("-rp", "--reg_pointer", type=str, help="Register address to write to in HEX format.")
    parser.add_argument("-rp_len", "--num_addr_byte", type=int, help="Set the number of Address bytes")

    parser.add_argument("-rv", "--reg_value", type=str, help="Register value to write in HEX format.")
    parser.add_argument("-rv_len", "--num_data_byte", type=int, help="Set the number of Data bytes")

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
                        handlers=[
                                  logging.StreamHandler(sys.stdout),
                                  logging.FileHandler(filename=fq_fn)
                                  ]
                        )
    scl = args.scl_pin
    sda = args.sda_pin
    fast_clk = int(400e3)
    slow_clk = int(100e3)

    logging.info("Starting the I2C Communication Test for SmartWave")

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
            i2c_dev_addr = i2c_addr_sweep(i2c, addr_lower=args.addr_lower, addr_upper=args.addr_upper)
            if i2c_dev_addr is None:
                logging.debug("Connection was unsuccessful.")
                logging.debug("Reducing the I2C clock speed to 100kHz and try to reconnect")
                i2c.clockSpeed = slow_clk
                logging.debug(f"I2C is running at {i2c.clockSpeed // 1e3} kHz")
                i2c_dev_addr = i2c_addr_sweep(i2c, addr_lower=args.addr_lower, addr_upper=args.addr_upper)
                if i2c_dev_addr is None:
                    logging.debug("Connection was unsuccessful.")
                    logging.debug("Swapping the SDA / SCL lines and trying to reconnect to device.")
                    i2c.delete()
                    i2c = sw.createI2CConfig(sda, scl, slow_clk)
                    i2c_dev_addr = i2c_addr_sweep(i2c, addr_lower=args.addr_lower, addr_upper=args.addr_upper)
                    if i2c_dev_addr is None:
                        logging.error("Couldn't reach device. Terminating code.")
                        raise ConnectionError("Terminating code.")

                    """
                    logging.debug("Please swap the SDA / SCL lines and retry")  # TODO: Automate (?)
                    retry = input("Press 'R' to retry or 'Q' to quit: ")
                    if retry.upper() == 'R':
                        i2c_dev_addr = i2c_addr_sweep(i2c, addr_lower=args.addr_lower, addr_upper=args.addr_upper)
                        if i2c_dev_addr is None:
                            logging.error("Couldn't reach device. Terminating code.")
                            raise ValueError("Terminating code.")
                    else:
                        logging.error("Couldn't reach device. Terminating code.")
                        raise ValueError("Terminating code.")
                    """

            if args.unique_id:
                logging.info(f"Read target specific register for device ID with address: {i2c_dev_addr:#0x}")
                hex_id = args.unique_id.split('x')[-1]
                if len(hex_id) % 2:
                    hex_id = "".join(['0', hex_id])
                unique_id = bytes.fromhex(hex_id)
                read_dev_id(i2c, i2c_dev_addr, unique_id)

            if args.reg_pointer:
                logging.info("Perform a register write / read operation on target device.")
                hex_addr = args.reg_pointer.split('x')[-1]
                if len(hex_addr) % 2:
                    hex_addr = "".join(['0', hex_addr])
                reg_pointer = bytes.fromhex(hex_addr)
                if args.num_addr_byte:
                    addr_length = int(args.num_addr_byte)
                else:
                    addr_length = len(reg_pointer)

                hex_val = args.reg_value.split('x')[-1]
                if len(hex_val) % 2:
                    hex_val = "".join(['0', hex_val])
                reg_value = bytes.fromhex(hex_val)
                if args.num_data_byte:
                    data_length = int(args.num_data_byte)
                else:
                    data_length = len(reg_value)

                register_r_w(i2c, i2c_dev_addr, reg_pointer, reg_value, addr_length, data_length)

            logging.info(f"I2C checklist was successfully completed. "
                         f"The log files can be found at {os.path.abspath(directory)}")


if __name__ == "__main__":
    main()

"""
Script Name: i2c_comms_check.py
Description: Test script for I2C Communication Setup Support
Author: Adam Horvath
Company: semify GmbH
Copyright © 2024 semify GmbH. All rights reserved.
"""
import sys
import re
import os
import logging
import requests
import time
import argparse
import importlib.metadata

from datetime import datetime
from typing import Union, Optional
import numpy as np

from SmartWaveAPI import SmartWave
from fpga_reg import FPGA_Reg


def get_latest_version(package_name: str) -> str:
    """
    Helper function that checks the latest available version of a Python package.
    In this scenario we are only interested in the SmartWaveAPI

    :param package_name: Name of the python package.
    :return: Version number as string
    """
    url = f"https://pypi.org/pypi/{package_name}/json"
    response = requests.get(url)
    data = response.json()
    latest_version = data["info"]["version"]

    return latest_version


def check_data_type(data) -> Union[str, hex]:
    """
    Helper function that converts the data given by the user and returns it as a hex value

    :param data: Value provided by the user that could be either binary, hex, or integer
    :return: Data converted into hexadecimal format
    """
    try:
        # Try converting the value to an integer in base 2 (binary)
        return hex(int(data, 2))[2:]
    except ValueError:
        pass

    if data.startswith("0x"):
        # If yes, treat it as hexadecimal and return
        return data[2:]
    else:
        # Otherwise, assume it's an integer and convert
        try:
            return hex(int(data))[2:]
        except ValueError:
            # If conversion fails, return an error message
            return "Not a valid integer or hexadecimal"


def gpio_high_low(sw: SmartWave, gpio_a, gpio_b, pin_conf_a: int, pin_conf_b: int) -> None:
    """
    Test if SDA and SCL can be pulled-down or up.

    :param sw: SmartWave object used for accessing the FPGA's registers
    :param gpio_a: SmartWave GPIO_A object used to measure the input level on the selected pin
    :param gpio_b: SmartWave GPIO_B object used to measure the input level on the selected pin
    :param pin_conf_a: Used to enable to selected pin in the FPGA's register
    :param pin_conf_b: Used to enable to selected pin in the FPGA's register
    :return: None
    """

    errors = 0
    pin_0 = str(pin_conf_a)
    pin_1 = str(pin_conf_b)

    ############################################################################################
    # Select the desired pins by writing to the FPGA's register
    ############################################################################################
    localenv = FPGA_Reg.registers["wfg_pin_mux_top"]
    addr = localenv["OUTPUT_SEL_0"]["addr"]
    pingroup = 0
    pingroup |= 0 << localenv["OUTPUT_SEL_0"][pin_0]["LSB"]
    pingroup |= 0 << localenv["OUTPUT_SEL_0"][pin_1]["LSB"]
    sw.writeFPGARegister(addr, pingroup)

    ############################################################################################
    # SCL and SDA pulled up
    ############################################################################################
    logging.info("1.1 - 1.2 - Setting both SCL and SDA in pull-up mode.")
    addr = localenv["PULLUP_SEL_0"]["addr"]
    pingroup = 0
    pingroup |= 1 << localenv["PULLUP_SEL_0"][pin_0]["LSB"]
    pingroup |= 1 << localenv["PULLUP_SEL_0"][pin_1]["LSB"]
    sw.writeFPGARegister(addr, pingroup)
    time.sleep(500e-3)
    input_level_a = gpio_a.inputLevel
    input_level_b = gpio_b.inputLevel

    logging.info(f"1.1 - Input level of SCL pin: {input_level_a} with pullup enabled.")
    logging.info(f"1.2 - Input level of SDA pin: {input_level_b} with pullup enabled.")

    if not input_level_a:
        logging.error("1.1 - The SCL pin is shorted to GND")
        errors += 1
    if not input_level_b:
        logging.error("1.2 - The SDA pin is shorted to GND")
        errors += 1

    ############################################################################################
    # SCL and SDA pulled down
    ############################################################################################
    logging.info("1.3 - 1.4 - Set both SCL and SDA in pull-down mode.")
    addr = localenv["PULLUP_SEL_0"]["addr"]
    pingroup = 0
    pingroup |= 5 << localenv["PULLUP_SEL_0"][pin_0]["LSB"]
    pingroup |= 5 << localenv["PULLUP_SEL_0"][pin_1]["LSB"]
    sw.writeFPGARegister(addr, pingroup)

    time.sleep(500e-3)
    input_level_a = gpio_a.inputLevel
    input_level_b = gpio_b.inputLevel

    logging.info(f"1.3 - Input level of SCL pin: {input_level_a} with pull-down enabled")
    logging.info(f"1.4 - Input level of SDA pin: {input_level_b} with pull-down enabled")

    if input_level_a:
        logging.error("1.3 - The SCL pin is shorted to VCC")
        errors += 1
    if input_level_b:
        logging.error("1.4 - The SDA pin is shorted to VCC")
        errors += 1

    if errors > 0:
        exit("1 - Terminating code.")


def gpio_short(sw, gpio_a, gpio_b, pin_conf_a, pin_conf_b) -> None:
    """
    Test if there's a short between the SCL and SDA lines

    :param sw: SmartWave object used for accessing the FPGA's registers
    :param gpio_a: SmartWave GPIO_A object used to measure the input level on the selected pin
    :param gpio_b: SmartWave GPIO_B object used to measure the input level on the selected pin
    :param pin_conf_a: Used to enable to selected pin in the FPGA's register
    :param pin_conf_b: Used to enable to selected pin in the FPGA's register
    :return: None
    """

    ############################################################################################
    # Select the desired pins by writing to the FPGA's register
    ############################################################################################
    pin_0 = str(pin_conf_a)
    pin_1 = str(pin_conf_b)
    localenv = FPGA_Reg.registers["wfg_pin_mux_top"]
    addr = localenv["OUTPUT_SEL_0"]["addr"]
    pingroup = 0
    pingroup |= 0 << localenv["OUTPUT_SEL_0"][pin_0]["LSB"]
    pingroup |= 0 << localenv["OUTPUT_SEL_0"][pin_1]["LSB"]
    sw.writeFPGARegister(addr, pingroup)

    ############################################################################################
    # SCL pulled low and SDA pulled high
    ############################################################################################
    logging.info("2.1 - Set SCL low and SDA high.")
    addr = localenv["PULLUP_SEL_0"]["addr"]
    pingroup = 0
    pingroup |= 5 << localenv["PULLUP_SEL_0"][pin_0]["LSB"]
    pingroup |= 1 << localenv["PULLUP_SEL_0"][pin_1]["LSB"]
    sw.writeFPGARegister(addr, pingroup)
    time.sleep(500e-3)
    input_level_a = gpio_a.inputLevel
    input_level_b = gpio_b.inputLevel
    logging.info(f"2.1 - Output level of SCL pin: {input_level_a}")
    logging.info(f"2.1 - Output level of SDA pin: {input_level_b}")

    if input_level_a == input_level_b:
        logging.critical("2.1 - There is a short between the SCL and SDA lines.")
        exit("2.1 - Terminating code.")

    ############################################################################################
    # SCL pulled high and SDA pulled low
    ############################################################################################
    logging.info("2.2 - Set SCL high and SDA low.")
    pingroup = 0
    pingroup |= 1 << localenv["PULLUP_SEL_0"][pin_0]["LSB"]
    pingroup |= 5 << localenv["PULLUP_SEL_0"][pin_1]["LSB"]
    sw.writeFPGARegister(addr, pingroup)
    time.sleep(500e-3)
    input_level_a = gpio_a.inputLevel
    input_level_b = gpio_b.inputLevel
    logging.info(f"2.2 - Output level of SCL pin: {input_level_a}")
    logging.info(f"2.2 - Output level of SDA pin: {input_level_b}")

    if input_level_a == input_level_b:
        logging.critical("2.2 - There is a short between the SCL and SDA lines.")
        exit("2.2 - Terminating code.")

    ############################################################################################
    # Re-enable the pull-ups for the I2C communication check
    ############################################################################################
    pingroup = 0
    pingroup |= 1 << localenv["PULLUP_SEL_0"][pin_0]["LSB"]
    pingroup |= 1 << localenv["PULLUP_SEL_0"][pin_1]["LSB"]
    sw.writeFPGARegister(addr, pingroup)


def i2c_addr_sweep(i2c, addr_lower: int, addr_upper: int) -> Union[None, list]:
    """
    Sweep all the possible I2C addresses and wait for the ACK.

    :param i2c: SmartWave I2C object
    :param addr_lower: Lower value for the I2C address sweep
    :param addr_upper: Upper value for the I2C address sweep
    :return: device specific I2C address
    """

    ############################################################################################
    # Check if the lower and upper address range is set correctly, and modify if needed
    ############################################################################################
    if addr_lower < 0:
        logging.warning("4.1 - Minimum value for the lower range can't be a negative number!")
        logging.debug("4.1 - Resetting the lower address value to the default 0.")
        addr_lower = 0

    if addr_upper > 127:
        logging.warning("4.1 - Maximum value for the upper range can't be greater than 127!")
        logging.debug("4.1 - Resetting the upper address value to the default 127.")
        addr_upper = 127

    if addr_upper < addr_lower:
        logging.warning("4.1 - The upper value can't be less than the lower value!")
        logging.debug("4.1 - Swapping the upper value with the lower value.")
        addr_swap = addr_upper
        addr_upper = addr_lower
        addr_lower = addr_swap
        logging.info(f"4.1 - The new lower value is: {addr_lower:#0x} and the new upper value is: {addr_upper:#0x}.")

    logging.info(
        f"4.1 - Trying to find the I2C address of the device within the range of {addr_lower:#0x} and {addr_upper:#0x}")

    i2c_addr = []
    dummy_byte = (0).to_bytes(1, 'big')
    i2c_addr_list = np.arange(addr_lower, addr_upper + 1)

    ############################################################################################
    # Check a single address passed by the user
    ############################################################################################
    if len(i2c_addr_list) == 1:
        i2c.write(int(i2c_addr_list[0]), dummy_byte)
        i2c_data = i2c.read(int(i2c_addr_list[0]), 1)
        if i2c_data.ack_device_id is None:
            logging.warning("4.1 - No device is connected to SmartWave.")
            logging.warning("4.1 - Check if all the wires are properly connected.")
            exit("4.1 - Terminating code")
        elif i2c_data.ack_device_id is False:
            logging.warning("4.1 - Couldn't reach device.")
        else:
            i2c_addr.append(int(i2c_addr_list[0]))
            logging.info(f"4.1 - Connection was successful. I2C address is: {i2c_addr[0]:#0x}")

    ############################################################################################
    # Sweep the possible addresses within the given range
    ############################################################################################
    else:
        connected = False
        for addr in range(len(i2c_addr_list)):
            i2c.write(int(i2c_addr_list[addr]), dummy_byte)
            i2c_data = i2c.read(int(i2c_addr_list[addr]), 1)
            if i2c_data.ack_device_id is None:
                logging.warning("4.1 - No device is connected to SmartWave.")
                logging.warning("4.1 - Check if all the wires are properly connected.")
                exit("4.1 - Terminating code")
            elif i2c_data.ack_device_id is False:
                if i2c_addr_list[addr] == i2c_addr_list[-1] and not i2c_addr:
                    logging.warning("4.1 - Couldn't reach device.")
            else:
                i2c_addr.append(int((i2c_addr_list[addr])))
                connected = True
        if connected:
            logging.info(f"4.1 - Connection was successful. {len(i2c_addr)} devices were found. "
                         "List of I2C Addresses: %s", ', '.join(hex(addr) for addr in i2c_addr))
    return i2c_addr


def register_r_w(i2c, i2c_addr: int, reg_pointer: bytes, reg_val: Optional[bytes] = None,
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

    ############################################################################################
    # Convert the register address to the correct length
    ############################################################################################
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

    ###########################################################################################
    # If register value is not set, then only read out the content of the specified register
    ###########################################################################################
    if reg_val is None:
        reg_read_back = i2c.readRegister(i2c_addr, addr_to_write.to_bytes(addr_length, 'big'), data_length)
        data_read_back = 0
        max_shift = (data_length - 1) * 8
        for pos in range(data_length):
            data_read_back |= reg_read_back[pos] << (max_shift - (pos * 8))
        logging.info(f"5.1 - Value read back: {data_read_back:#0x} from register address: {reg_pointer[0]:#0x}")

    ############################################################################################
    # Modify the register value then do a read-back and compare the results
    ############################################################################################
    else:
        # Convert the register data to the correct length
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

        ############################################################################################
        # Register write
        ############################################################################################
        i2c.writeRegister(i2c_addr, addr_to_write.to_bytes(addr_length, 'big'),
                          data_to_write.to_bytes(data_length, 'big'))
        logging.info(f"5.2 - Value written: {data_to_write:#0x} to register address {reg_pointer[0]:#0x}")

        ############################################################################################
        # Register read
        ############################################################################################
        reg_read_back = i2c.readRegister(i2c_addr, addr_to_write.to_bytes(addr_length, 'big'), data_length)
        data_read_back = 0
        max_shift = (data_length - 1) * 8
        for pos in range(data_length):
            data_read_back |= reg_read_back[pos] << (max_shift - (pos * 8))
        logging.info(f"5.2 - Value read back: {data_read_back:#0x} from register address {reg_pointer[0]:#0x}")

        if data_to_write != data_read_back:
            logging.error("5.2 - The value read back from the register does not match the written value!")
            exit()


def main():
    """
    Setup I2C communication on SmartWave and perform a complete check:

    - SDA, SCL can be pull-down or pull-up
    - no shorts between SCL and SDA
    - send command to target device and check for ACK
    - check for correct target
    :return: none
    """

    ############################################################################################
    # Command line arguments provided by the user
    ############################################################################################
    parser = argparse.ArgumentParser(description="Access Registers.")
    parser.add_argument("-update", "--version_update", type=int, help="Update the SmartWave FPGA and Firmware to the"
                                                                      "latest release.", default=0)

    parser.add_argument("-log", "--log_location", type=str, help="User defined location for log files")

    parser.add_argument("-gpio", "--gpio_test", type=int, help="Test is the pins can be pulled high and low.",
                        default=1)

    parser.add_argument("-scl", "--scl_pin", type=str, help="Select the desired SCL Pin on SmartWave", default='A1')
    parser.add_argument("-sda", "--sda_pin", type=str, help="Select the desired SDA Pin on SmartWave", default='A2')

    parser.add_argument("-lower", "--addr_lower", type=str, help="Select the lower address value "
                                                                 "for the I2C address sweep", default='0')
    parser.add_argument("-upper", "--addr_upper", type=str, help="Select the upper address value "
                                                                 "for the I2C address sweep", default='127')

    parser.add_argument("-addr", "--user_addr", type=str, help="Select which device should be accessed for register"
                                                               "read/write operation")

    parser.add_argument("-rw", "--reg_read_write", type=int, help="Read/Write flag for register access.")

    parser.add_argument("-rp", "--reg_pointer", type=str, help="Register address to write to in HEX format.")
    parser.add_argument("-rp_len", "--num_addr_byte", type=int, help="Set the number of Address bytes")

    parser.add_argument("-rv", "--reg_value", type=str, help="Register value to write in HEX format.")
    parser.add_argument("-rv_len", "--num_data_byte", type=int, help="Set the number of Data bytes")

    args = parser.parse_args()

    ############################################################################################
    # Create directory to save the log files
    ############################################################################################
    if args.log_location:
        directory = args.log_location
    else:
        directory = "./i2c_check_logs"

    if not os.path.exists(directory):
        os.mkdir(directory)

    ############################################################################################
    # Basic configuration for logging
    ############################################################################################
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
    original_log_level = logging.getLogger().getEffectiveLevel()

    ############################################################################################
    # Check if the SmartWaveAPI is the latest available version
    ############################################################################################
    try:
        version = importlib.metadata.version("SmartWaveAPI")
        logging.info(f"SmartWaveAPI Version: {version}")
        logging.getLogger().setLevel(logging.INFO)
        latest_version = get_latest_version("SmartWaveAPI")
        logging.getLogger().setLevel(original_log_level)
        if version != latest_version:
            logging.warning("SmartWaveAPI is outdated! Some functionalities might not work."
                            "It is recommended to update using pip install --upgrade SmartWaveAPI")
    except importlib.metadata.PackageNotFoundError:
        logging.error("SmartWaveAPI is not installed.")

    ############################################################################################
    # Parameters for I2C object configuration
    ############################################################################################
    scl = args.scl_pin
    sda = args.sda_pin
    fast_clk = int(400e3)
    slow_clk = int(100e3)

    logging.info("Starting the I2C Communication Test for SmartWave")

    fpga_outdated = False
    ############################################################################################
    # Setup connection to SmartWave
    ############################################################################################
    with SmartWave().connect() as sw:
        logging.info("Successfully connected to SmartWave")
        sw.infoCallback = lambda hw, uc, fpga, flashID: (
            setattr(sw, "fpga_outdated", True),  # Raise the flag if FPGA version is outdated
            logging.warning("FPGA version is outdated, some functions may not work")
        ) if fpga != (2, 2, 0) else (
            setattr(sw, "fpga_outdated", False),  # Reset the flag if FPGA version is up-to-date
            logging.info(f"Hardware version: {hw}\tMicrocontroller version: {uc}\tFPGA version: {fpga}")
        )

        ############################################################################################
        # Update the FPGA bitstream and Microcontroller Firmware, if version update is enabled.
        ############################################################################################
        if args.version_update == 1:
            sw.disconnect()
            with SmartWave().connect() as sw:
                sw.updateFPGABitstream()
                time.sleep(2)
                sw.firmwareUpdateStatusCallback = lambda isUc, status: logging.info(
                    "%s update status: %d%%" % ("Microcontroller" if isUc else "FPGA", status))
                sw.updateFirmware()
            time.sleep(2)  # Wait for all the updates to complete before reconnecting to SmartWave.
            sw = SmartWave().connect()
            fpga_outdated = False

        if fpga_outdated and (args.version_update == 0):
            logging.warning("The current version of the FPGA does not support the pull-down configuration on the GPIOs."
                            "The script will skip the SCL and SDA line checks and progresses to the I2C communication "
                            "check.")

        ############################################################################################
        # Check the SCL and SDA lines
        ############################################################################################
        elif (fpga_outdated is False) and (args.gpio_test == 1):
            with sw.createGPIO(pin_name=scl, name="SCL") as gpio_A:
                with sw.createGPIO(pin_name=sda, name="SDA") as gpio_B:
                    logging.info(f"Instantiate a GPIO object on the specified target pins. SCL: {scl} // SDA: {sda}")
                    logging.info("1 - Test whether SCL and SDA can be pulled-down and pulled-up.")
                    pin_conf_a = int(re.findall(r'\d+', scl)[0]) - 1
                    pin_conf_b = int(re.findall(r'\d+', sda)[0]) - 1
                    gpio_high_low(sw, gpio_A, gpio_B, pin_conf_a, pin_conf_b)
                    logging.info("2 - Check for shorts between SCL and SDA")
                    gpio_short(sw, gpio_A, gpio_B, pin_conf_a, pin_conf_b)
                    logging.info("The SCL and SDA line checks have been successfully completed.")
                    logging.info("Moving on to the I2C communication setup check.")

        ############################################################################################
        # Start the I2C communication check
        ############################################################################################
        with sw.createI2CConfig(sda_pin_name=sda, scl_pin_name=scl, clock_speed=fast_clk) as i2c:
            logging.info(f"4 - SCL is set to pin: {scl} | SDA is set to pin: {sda} "
                         f"| I2C clock running at {fast_clk // 1e3} kHz")
            logging.info("4.1 - Trying to connect to the target device")
            addr_lower = check_data_type(args.addr_lower)
            addr_lower = int(addr_lower, 16)
            addr_upper = check_data_type(args.addr_upper)
            addr_upper = int(addr_upper, 16)
            i2c_dev_addr = i2c_addr_sweep(i2c, addr_lower=addr_lower, addr_upper=addr_upper)
            if not i2c_dev_addr:
                logging.debug("4.1 - Connection was unsuccessful.")
                logging.debug("4.2 - Reducing the I2C clock speed to 100kHz and try to reconnect")
                i2c.clockSpeed = slow_clk
                logging.debug(f"4.2 - I2C is running at {i2c.clockSpeed // 1e3} kHz")
                i2c_dev_addr = i2c_addr_sweep(i2c, addr_lower=addr_lower, addr_upper=addr_upper)
                if not i2c_dev_addr:
                    logging.debug("4.2 - Connection was unsuccessful.")
                    logging.debug("4.3 - Swapping the SDA / SCL lines and trying to reconnect to device.")
                    i2c.delete()
                    i2c = sw.createI2CConfig(scl_pin_name=sda, sda_pin_name=scl, clock_speed=slow_clk)
                    i2c_dev_addr = i2c_addr_sweep(i2c, addr_lower=addr_lower, addr_upper=addr_upper)
                    if not i2c_dev_addr:
                        logging.error("4.3 - Couldn't reach device. Terminating code.")
                        exit()

            ############################################################################################
            # Access the user specified register and read out its content
            ############################################################################################
            if args.reg_pointer:
                logging.info("5 - Check for the correct target device by accessing a known register.")
                reg_value = None
                if args.reg_read_write:
                    logging.info(f"5.1 - Perform a register read operation on device {i2c_dev_addr[0]:#0x}")

                target_addr = check_data_type(args.reg_pointer)
                if len(target_addr) % 2:
                    target_addr = "".join(['0', target_addr])
                reg_pointer = bytes.fromhex(target_addr)

                if args.num_addr_byte:
                    addr_length = int(args.num_addr_byte)
                else:
                    addr_length = len(reg_pointer)
                if args.num_data_byte:
                    data_length = int(args.num_data_byte)
                else:
                    logging.debug("5.1 - Length of the data value wasn't set. Using default value of one byte.")
                    data_length = 1

                ############################################################################################
                # Modify the content of the specified register and read it back for validation
                ############################################################################################
                if not args.reg_read_write:
                    if args.reg_value is None:
                        logging.warning("5.2 - Cannot perform register write if value is not given")
                        exit(f"5.2 - Terminating code.")
                    else:
                        hex_val = check_data_type(args.reg_value)
                        if len(hex_val) % 2:
                            hex_val = "".join(['0', hex_val])
                        reg_value = bytes.fromhex(hex_val)
                        if args.num_data_byte:
                            data_length = int(args.num_data_byte)
                        else:
                            data_length = len(reg_value)

                ############################################################################################
                # Perform a register access on the user defined device
                ############################################################################################
                if args.user_addr:
                    target_addr = check_data_type(args.user_addr)
                    target_addr = int(target_addr, 16)
                    target_found = False
                    logging.info("5.2 - Performing a read/write operation on the selected device with address "
                                 f"{target_addr:#0x}")
                    for idx, dev in enumerate(i2c_dev_addr):
                        if dev == target_addr:
                            target_found = True
                            register_r_w(i2c, i2c_dev_addr[idx], reg_pointer, reg_value, addr_length, data_length)
                        if not target_found and dev == i2c_dev_addr[-1]:
                            logging.warning("5.2 - Target not found. Make sure the device address is correct.")
                            exit()

                ############################################################################################
                # Perform a register access on the first device in the i2c_dev_addr list
                ############################################################################################
                else:
                    logging.info(f"5.2 - Perform a register write and read operation on device {i2c_dev_addr[0]:#0x}.")
                    register_r_w(i2c, i2c_dev_addr[0], reg_pointer, reg_value, addr_length, data_length)

            logging.info(f"I2C checklist was successfully completed. "
                         f"The log files can be found at {os.path.abspath(directory)}")


if __name__ == "__main__":
    main()

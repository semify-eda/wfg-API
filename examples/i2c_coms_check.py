"""
Test script to check I2C communication setup
"""
import sys
import re
import os
import logging
import time
import argparse
import pkg_resources

from datetime import datetime
from typing import Union, Optional
import numpy as np

from SmartWaveAPI import SmartWave
from fpga_reg import FPGA_Reg


def check_data_type(data):
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

    localenv = FPGA_Reg.registers["wfg_pin_mux_top"]
    addr = localenv["OUTPUT_SEL_0"]["addr"]
    pingroup = 0
    pingroup |= 0 << localenv["OUTPUT_SEL_0"][pin_0]["LSB"]
    pingroup |= 0 << localenv["OUTPUT_SEL_0"][pin_1]["LSB"]
    sw.writeFPGARegister(addr, pingroup)

    ###########################################
    # SCL and SDA pulled up
    ###########################################
    logging.info("1.1 and 1.3 Setting both SCL and SDA in pullup mode.")
    addr = localenv["PULLUP_SEL_0"]["addr"]
    pingroup = 0
    pingroup |= 1 << localenv["PULLUP_SEL_0"][pin_0]["LSB"]
    pingroup |= 1 << localenv["PULLUP_SEL_0"][pin_1]["LSB"]
    sw.writeFPGARegister(addr, pingroup)
    time.sleep(500e-3)
    input_level_a = gpio_a.inputLevel
    input_level_b = gpio_b.inputLevel

    logging.info(f"Input level of SCL pin: {input_level_a} with pullup enabled.")
    logging.info(f"Input level of SDA pin: {input_level_b} with pullup enabled.")

    if not input_level_a:
        logging.error("The SCL pin is shorted to GND")
        errors += 1
    if not input_level_b:
        logging.error("The SDA pin is shorted to GND")
        errors += 1

    ###########################################
    # SCL and SDA pulled down
    ###########################################
    logging.info("1.2 and 1.4 Set both SCL and SDA in pull-down mode.")
    addr = localenv["PULLUP_SEL_0"]["addr"]
    pingroup = 0
    pingroup |= 5 << localenv["PULLUP_SEL_0"][pin_0]["LSB"]
    pingroup |= 5 << localenv["PULLUP_SEL_0"][pin_1]["LSB"]
    sw.writeFPGARegister(addr, pingroup)

    time.sleep(500e-3)
    input_level_a = gpio_a.inputLevel
    input_level_b = gpio_b.inputLevel

    logging.info(f"Input level of SCL pin: {input_level_a} with pulldown enabled")
    logging.info(f"Input level of SDA pin: {input_level_b} with pulldown enabled")

    if input_level_a:
        logging.error("The SCL pin is shorted to VCC")
        errors += 1
    if input_level_b:
        logging.error("The SDA pin is shorted to VCC")
        errors += 1

    if errors > 0:
        exit("Terminating code.")


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

    pin_0 = str(pin_conf_a)
    pin_1 = str(pin_conf_b)
    localenv = FPGA_Reg.registers["wfg_pin_mux_top"]
    addr = localenv["OUTPUT_SEL_0"]["addr"]
    pingroup = 0
    pingroup |= 0 << localenv["OUTPUT_SEL_0"][pin_0]["LSB"]
    pingroup |= 0 << localenv["OUTPUT_SEL_0"][pin_1]["LSB"]
    sw.writeFPGARegister(addr, pingroup)

    logging.info("2.1 - Set SCL low and SDA high.")
    addr = localenv["PULLUP_SEL_0"]["addr"]
    pingroup = 0
    pingroup |= 5 << localenv["PULLUP_SEL_0"][pin_0]["LSB"]
    pingroup |= 1 << localenv["PULLUP_SEL_0"][pin_1]["LSB"]
    sw.writeFPGARegister(addr, pingroup)
    time.sleep(500e-3)
    input_level_a = gpio_a.inputLevel
    input_level_b = gpio_b.inputLevel
    logging.info(f"Output level of SCL pin: {input_level_a}")
    logging.info(f"Output level of SDA pin: {input_level_b}")

    if input_level_a == input_level_b:
        logging.critical("There is a short between the SCL and SDA lines.")
        exit("Terminating code.")

    logging.info("2.2 - Set SCL high and SDA low.")
    pingroup = 0
    pingroup |= 1 << localenv["PULLUP_SEL_0"][pin_0]["LSB"]
    pingroup |= 5 << localenv["PULLUP_SEL_0"][pin_1]["LSB"]
    sw.writeFPGARegister(addr, pingroup)
    time.sleep(500e-3)
    input_level_a = gpio_a.inputLevel
    input_level_b = gpio_b.inputLevel
    logging.info(f"Output level of SCL pin: {input_level_a}")
    logging.info(f"Output level of SDA pin: {input_level_b}")

    if input_level_a == input_level_b:
        logging.critical("There is a short between the SCL and SDA lines.")
        exit("Terminating code.")

    # Re-enable the pullups for the I2C communication check
    pingroup = 0
    pingroup |= 1 << localenv["PULLUP_SEL_0"][pin_0]["LSB"]
    pingroup |= 1 << localenv["PULLUP_SEL_0"][pin_1]["LSB"]
    sw.writeFPGARegister(addr, pingroup)


def i2c_addr_sweep(i2c, addr_lower: int, addr_upper: int, multi_dev: bool) -> Union[None, list]:
    """
    Sweep all the possible I2C addresses and wait for the ACK.

    :param i2c: SmartWave I2C object
    :param addr_lower: Lower value for the I2C address sweep
    :param addr_upper: Upper value for the I2C address sweep
    :param multi_dev: Check if we are looking for a single or multiple devices
    :return: device specific I2C address
    """
    if addr_lower < 0:
        logging.warning("Minimum value for the lower range can't be a negative number!")
        logging.debug("Resetting the lower address value to the default 0.")
        addr_lower = 0

    if addr_upper > 127:
        logging.warning("Maximum value for the upper range can't be greater than 127!")
        logging.debug("Resetting the upper address value to the default 127.")
        addr_upper = 127

    if addr_upper < addr_lower:
        logging.warning("The upper value can't be less than the lower value!")
        logging.debug("Swapping the upper value with the lower value.")
        addr_swap = addr_upper
        addr_upper = addr_lower
        addr_lower = addr_swap
        logging.info(f"The new lower value is: {addr_lower} and the new upper value is: {addr_upper}.")

    logging.info(f"Trying to find the I2C address of the device within the range of {addr_lower} and {addr_upper}")

    i2c_addr = []
    dummy_byte = (0).to_bytes(1, 'big')
    i2c_addr_list = np.arange(addr_lower, addr_upper + 1)

    # Check a single address passed by the user
    if len(i2c_addr_list) == 1:
        i2c.write(int(i2c_addr_list[0]), dummy_byte)
        i2c_data = i2c.read(int(i2c_addr_list[0]), 1)
        if i2c_data.ack_device_id is None:
            logging.warning("No device is connected to SmartWave.")
            logging.warning("Check if all the wires are properly connected.")
            exit("Terminating code")
        elif i2c_data.ack_device_id is False:
            logging.warning("Couldn't reach device.")
        else:
            i2c_addr.append(int(i2c_addr_list[0]))
            logging.info(f"Connection was successful. I2C address is: {i2c_addr[0]:#0x}")

    # Sweep the possible addresses within the given range
    else:
        if multi_dev:           # If multiple devices are connected to the I2C bus
            for addr in range(len(i2c_addr_list)):
                i2c.write(int(i2c_addr_list[addr]), dummy_byte)
                i2c_data = i2c.read(int(i2c_addr_list[addr]), 1)
                if i2c_data.ack_device_id is None:
                    logging.warning("No device is connected to SmartWave.")
                    logging.warning("Check if all the wires are properly connected.")
                    exit("Terminating code")
                if i2c_data.ack_device_id is False:
                    if addr == i2c_addr_list[-1]:
                        logging.warning("Couldn't reach device.")
                    continue
                i2c_addr.append(int((i2c_addr_list[addr])))
            logging.info("Connection was successful. List of I2C Addresses: %s",
                         ', '.join(hex(addr) for addr in i2c_addr))

        else:                   # If we are only looking for a single device
            for addr in range(len(i2c_addr_list)):
                i2c.write(int(i2c_addr_list[addr]), dummy_byte)
                i2c_data = i2c.read(int(i2c_addr_list[addr]), 1)
                if i2c_data.ack_device_id is None:
                    logging.warning("No device is connected to SmartWave.")
                    logging.warning("Check if all the wires are properly connected.")
                    exit("Terminating code")
                if i2c_data.ack_device_id is False:
                    if addr == i2c_addr_list[-1]:
                        logging.warning("Couldn't reach device.")
                    continue
                i2c_addr.append(int(i2c_addr_list[addr]))
                logging.info(f"Connection was successful. I2C address is: {i2c_addr[0]:#0x}")
                break

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

    # If register value is not set, then only read out the content of the specified register
    if reg_val is None:
        reg_read_back = i2c.readRegister(i2c_addr, addr_to_write.to_bytes(addr_length, 'big'), data_length)
        data_read_back = 0
        max_shift = (data_length - 1) * 8
        for pos in range(data_length):
            data_read_back |= reg_read_back[pos] << (max_shift - (pos * 8))
        logging.info(f"Value read back: {data_read_back:#0x} from register address: {reg_pointer[0]:#0x}")

    # Modify the register value then do a readout and compare the results
    else:
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
        i2c.writeRegister(i2c_addr, addr_to_write.to_bytes(addr_length, 'big'),
                          data_to_write.to_bytes(data_length, 'big'))
        logging.info(f"Value written: {data_to_write:#0x} to register address {reg_pointer[0]:#0x}")

        # Register read
        reg_read_back = i2c.readRegister(i2c_addr, addr_to_write.to_bytes(addr_length, 'big'), data_length)
        data_read_back = 0
        max_shift = (data_length - 1) * 8
        for pos in range(data_length):
            data_read_back |= reg_read_back[pos] << (max_shift - (pos * 8))
        logging.info(f"Value read back: {data_read_back:#0x} from register address {reg_pointer[0]:#0x}")

        if data_to_write != data_read_back:
            logging.error("The value read back from the register does not match the written value!")
            exit()


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
    parser.add_argument("-log", "--log_location", type=str, help="User defined location for log files")

    parser.add_argument("-scl", "--scl_pin", type=str, help="Select the desired SCL Pin on SmartWave", default='A1')
    parser.add_argument("-sda", "--sda_pin", type=str, help="Select the desired SDA Pin on SmartWave", default='A2')

    parser.add_argument("-multi", "--multiple_dev", type=bool,
                        help="Look for multiple devices on the I2C bus", default=False)
    parser.add_argument("-lower", "--addr_lower", type=int, help="Select the lower address value "
                                                                 "for the I2C address sweep", default=0)
    parser.add_argument("-upper", "--addr_upper", type=int, help="Select the upper address value "
                                                                 "for the I2C address sweep", default=127)

    parser.add_argument("-rw", "--reg_read_write", type=int, help="Read/Write flag for register access.")

    parser.add_argument("-rp", "--reg_pointer", type=str, help="Register address to write to in HEX format.", default="0x1")
    parser.add_argument("-rp_len", "--num_addr_byte", type=int, help="Set the number of Address bytes")

    parser.add_argument("-rv", "--reg_value", type=str, help="Register value to write in HEX format.")
    parser.add_argument("-rv_len", "--num_data_byte", type=int, help="Set the number of Data bytes")

    args = parser.parse_args()

    # Create directory to save the log files
    if args.log_location:
        directory = args.log_location
    else:
        directory = "./i2c_check_logs"

    if not os.path.exists(directory):
        os.mkdir(directory)

    # Basic configuration for logging
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
    # Parameters for I2C object configuration
    scl = args.scl_pin
    sda = args.sda_pin
    fast_clk = int(400e3)
    slow_clk = int(100e3)

    logging.info("Starting the I2C Communication Test for SmartWave")

    # Setup connection to SmartWave
    with SmartWave().connect() as sw:
        logging.info("Successfully connected to SmartWave")
        installed_packages = pkg_resources.working_set
        for package in installed_packages:
            if package.key == "smartwaveapi":
                logging.info(f"SmartWaveAPI Version: {package.version}")
                break
        sw.infoCallback = lambda hw, uc, fpga, flashID: logging.info(
            f"Hardware version: {hw}\tMicrocontroller version: {uc}\tFPGA version: {fpga}\t")

        ###########################################
        # Check the SCL and SDA lines
        ###########################################
        with sw.createGPIO(pin_name=scl, name="SCL") as gpio_A:
            with sw.createGPIO(pin_name=sda, name="SDA") as gpio_B:
                logging.info(f"Instantiate a GPIO object on the specified target pins. SCL: {scl} // SDA: {sda}")
                logging.info("1. - Test whether SCL and SDA can be pulled-down and pulled-up.")
                pin_conf_a = int(re.findall(r'\d+', scl)[0]) - 1
                pin_conf_b = int(re.findall(r'\d+', sda)[0]) - 1
                gpio_high_low(sw, gpio_A, gpio_B, pin_conf_a, pin_conf_b)
                logging.info("2. - Check for shorts between SCL and SDA")
                gpio_short(sw, gpio_A, gpio_B, pin_conf_a, pin_conf_b)
                logging.info("The SCL and SDA line checks have been successfully completed.")
                logging.info("Moving on to the I2C communication setup check.")

        ###########################################
        # Start the I2C communication check
        ###########################################
        with sw.createI2CConfig(sda_pin_name=sda, scl_pin_name=scl, clock_speed=fast_clk) as i2c:
            logging.info(f"SCL is set to pin: {scl} | SDA is set to pin: {sda} "
                         f"| I2C clock running at {fast_clk // 1e3} kHz")
            logging.info("4.1 - Trying to connect to the target device")
            multi_dev = args.multiple_dev
            i2c_dev_addr = i2c_addr_sweep(i2c, addr_lower=args.addr_lower, addr_upper=args.addr_upper,
                                          multi_dev=multi_dev)
            if not i2c_dev_addr:
                logging.debug("Connection was unsuccessful.")
                logging.debug("4.2 - Reducing the I2C clock speed to 100kHz and try to reconnect")
                i2c.clockSpeed = slow_clk
                logging.debug(f"I2C is running at {i2c.clockSpeed // 1e3} kHz")
                i2c_dev_addr = i2c_addr_sweep(i2c, addr_lower=args.addr_lower, addr_upper=args.addr_upper,
                                              multi_dev=multi_dev)
                if not i2c_dev_addr:
                    logging.debug("Connection was unsuccessful.")
                    logging.debug("4.3 - Swapping the SDA / SCL lines and trying to reconnect to device.")
                    i2c.delete()
                    i2c = sw.createI2CConfig(scl_pin_name=sda, sda_pin_name=scl, clock_speed=slow_clk)
                    i2c_dev_addr = i2c_addr_sweep(i2c, addr_lower=args.addr_lower, addr_upper=args.addr_upper,
                                                  multi_dev=multi_dev)
                    if not i2c_dev_addr:
                        logging.error("Couldn't reach device. Terminating code.")
                        exit()

            # Access the user specified register and read out its content
            if args.reg_pointer:
                logging.info("5. - Check for the correct target device by accessing a known register.")
                reg_value = None
                if args.reg_read_write:
                    logging.info("5.1 - Perform a register read operation on the target device")

                hex_addr = check_data_type(args.reg_pointer)
                if len(hex_addr) % 2:
                    hex_addr = "".join(['0', hex_addr])
                reg_pointer = bytes.fromhex(hex_addr)

                if args.num_addr_byte:
                    addr_length = int(args.num_addr_byte)
                else:
                    addr_length = len(reg_pointer)
                if args.num_data_byte:
                    data_length = int(args.num_data_byte)
                else:
                    logging.debug("Length of the data value wasn't set. Using default value of one byte.")
                    data_length = 1

                # Modify the content of the specified register and read it back for validation
                if not args.reg_read_write:
                    logging.info("5.2 - Perform a register write and read operation on target device.")
                    if args.reg_value is None:
                        logging.warning("Cannot perform register write if value is not given")
                        exit(f"Terminating code.")
                    else:
                        hex_val = check_data_type(args.reg_value)
                        if len(hex_val) % 2:
                            hex_val = "".join(['0', hex_val])
                        reg_value = bytes.fromhex(hex_val)
                        if args.num_data_byte:
                            data_length = int(args.num_data_byte)
                        else:
                            data_length = len(reg_value)

                # Call the register read/write function with the user-defined values
                if args.multiple_dev:
                    logging.info("Performing a read/write operation of multiple devices is currently not supported")
                    logging.info("A single register access will be performed on the first device.")
                    register_r_w(i2c, i2c_dev_addr[0], reg_pointer, reg_value, addr_length, data_length)
                    # for dev in range(len(i2c_dev_addr)):
                    #     register_r_w(i2c, i2c_dev_addr[dev], reg_pointer, reg_value, addr_length, data_length)

                else:
                    register_r_w(i2c, i2c_dev_addr[0], reg_pointer, reg_value, addr_length, data_length)

            logging.info(f"I2C checklist was successfully completed. "
                         f"The log files can be found at {os.path.abspath(directory)}")


if __name__ == "__main__":
    main()

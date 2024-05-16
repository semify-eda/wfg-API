# I2C Communication Setup Support
A python script used to carry out basic I2C communication setup checks.

## Description
The script's objective is to validate the I2C communication setup of specified pins on SmartWave, ensuring their accurate 
setting as logic 1 or logic 0 values via pull-up or pull-down mode. Additionally, it facilitates the detection of 
potential shorts to VCC or GND, as well as any short circuits between SCL and SDA lines.

After completing these verifications, the script proceeds to establish connections with one or more devices linked to 
the I2C bus line. This involves scanning through all possible I2C addresses or within a range specified by the user.

Should a connection to the target device fail, the script first reduces the I2C clock speed to 100kHz. 
If connection issues persist, it attempts to resolve them by swapping the selected SCL and SDA lines on SmartWave 
and then reattempting the connection. If the problem persists despite these efforts, user intervention becomes necessary.

After establishing a successful connection with the target device, the user has the option to either read the content of
a known register or modify its content and then perform a read-back. This process ensures that both read and write 
operations can be executed effectively on the target device.

## Dependencies
- The script relies on the SmartWaveAPI package, which requires python version 3.
- There are other standard python packages that are required to run this script, which are added to `requirements.txt` 
- To install these packages, run the following command:
```bash
pip install -r requirements.txt
```

## Usage
The first thing to do is to ensure that SmartWave is securely connected to host PC. 
The script can be run from terminal by simply calling:
```bash
python i2c_comms_check.py
```
The script initially verifies whether the Firmware and FPGA versions are the latest available releases. If not, the 
user has the option to update them with the following command line argument when executing the script:
```bash
-update 1  # Update the Firmware and FPGA bitstream to the latest release
```
This option is disabled by default, to prevent overwriting any changes made by the user.

It is important to note that when multiple devices are connected to the same I2C bus, SmartWave may not be able to pull 
down the SCL/SDA lines, leading to a failure when checking for logic 0 levels. This occurs because the combined pull-up 
strength of the connected devices exceeds the pull-down resistor strength of SmartWave, maintaining the SCL/SDA line at 
logic 1.
If this is the case, the user can specify to skip the GPIO test with the following command line argument:
```bash
-gpio 0     # Bypass the GPIO tests
```

By default, the script will only execute the basic pin tests and the I2C address check using the default pin settings 
and address range. However, if the user wishes to modify the default values or run the register test, they can do so by 
specifying the desired options through the following command line arguments:
```bash
-scl A2 -sda A3     # Configure pin A2 to SCL and pin A3 to SDA
```
```bash
-lower 20 -upper 30   # Look for the device's I2C address within the range of 20-30 
```
It's important to note that if the lower and upper range are equal, the script will only verify whether that single 
address matches the device's address.

In case the user has multiple devices connected to the I2C bus, an extended address sweep can be performed.
This would find the I2C addresses of all the connected devices, and return it as a list.

If the user want to perform a register read/write operation, then they can use the following command line arguments:
```bash
-rw 1  # Read/write flag for register access
```
The default value of the read/write flag is 1, which will perform a register read, if the register pointer argument is given.

```bash
-rp 0x1  # Register pointer 
```
The register pointer is the address of the register that we want to investigate. The address value can be given as
an integer, hex or binary.

```bash
-rp_len 1  # Register pointer length in bytes
```
The length of the register pointer can be specified by using the -rp_len command line argument, or use the default value
of one byte. 

```bash
-rv 0x11FA  # Register value 
```
If the -rw flag is set to 0, i.e. write mode, we have to specify the data that we wish to write to the register.
This can be done by using the -rv argument, which is the register data value.

```bash
-rv_len 2  # Register value length in bytes
```
Similarly to the register pointer, we can also specify the number of bytes of data to write into the register. 
However, this value must also be specified when reading out the register content. Failure to do so may result in 
attempting to read fewer data than the actual content of the register, leading to an error.

### Logging
When running the I2C communication setup check,  the script logs all essential steps, simplifying user debugging in 
case of failures. The logging data is saved in the root directory as a `.log` file, though users can specify a different 
location using the following command line argument:
```bash
-log C:\i2c_check\logs  # Location where to save the log files
```

### Example
A complete run configuration could look like this:
```bash
python i2c_comms_check.py -update 0 -log C:\semify\i2c_logs -gpio 1 -scl A1 -sda A2 -lower 20 -upper 26 -rw 0 -rp 0x1 -rp_len 1 -rv 0x0101 -rv_len 2
```
This will disable the auto update (default setting) save the log files to the specified directory and enable the GPIO 
checks (default setting). Set up the SCL line on pin A1 and the SDA line on pin A2. 
The I2C address sweep will be done within the range of 20 to 26. Additionally, we will perform a write operation to the 
register address of 0x1, which has a length of one byte. The data we wish to write to this address is 0x0101 with a 
length of two bytes.

The user must ensure that the register address corresponds to a valid address of the connected device and supports
read/write capabilities. Additionally, it is essential to provide the correct length for both the address 
and data. Failure to do so may result in accessing and/or modifying an incorrect register.

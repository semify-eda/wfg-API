import serial
import serial.tools.list_ports
import threading
import time
import os

from typing import List, Union, Callable, Literal, Optional, Dict

from SmartWaveAPI.configitems import Pin, I2CDriver, Stimulus, Config, SPIDriver, GPIO
from SmartWaveAPI.configitems.i2cconfig import I2CConfig
from SmartWaveAPI.configitems.spiconfig import SPIConfig
from SmartWaveAPI.definitions import Command, Statusbit, ErrorCode, TriggerMode, PinOutputType


class SmartWave(object):
    """An instance of a SmartWave device. Keeps track of all available resources."""
    VID: int = 0x2341
    PID: int = 0x8071
    FPGAClockSpeed: int = 100e6
    FPGAClockDivided: int = FPGAClockSpeed / 0xffff  # slowest possible division

    SBLStart = 0x2000
    FirmwareStart = 0x9000
    FirmwareEnd = 0x18200
    FPGABitstreamStart = 0x0
    FPGABitstreamEnd = 0xfffffffffffff

    def __init__(self):
        """Create a new SmartWave instance."""
        self._serialPort = None

        self._availableI2CDrivers = [
            I2CDriver(self, 0),
            I2CDriver(self, 1),
        ]

        self._availableSPIDrivers = [
            SPIDriver(self, 0),
            SPIDriver(self, 1)
        ]

        self._availableStimuli = [
            Stimulus(self, 0),
            Stimulus(self, 1),
            Stimulus(self, 2),
            Stimulus(self, 3),
        ]

        self._availablePins = [
            Pin(self, "A", 1),
            Pin(self, "A", 2),
            Pin(self, "A", 3),
            Pin(self, "A", 4),

            Pin(self, "A", 7),
            Pin(self, "A", 8),
            Pin(self, "A", 9),
            Pin(self, "A", 10),

            Pin(self, "B", 1),
            Pin(self, "B", 2),
            Pin(self, "B", 3),
            Pin(self, "B", 4),

            Pin(self, "B", 7),
            Pin(self, "B", 8),
            Pin(self, "B", 9),
            Pin(self, "B", 10),
        ]

        # TODO check if this creates a reference or copies
        self._allPins: List[Pin] = []
        for pin in self._availablePins:
            self._allPins.append(pin)

        self.configEntries: List[Config] = []

        self._heartbeatThread: Union[threading.Thread, None] = None
        self._readingThread: Union[threading.Thread, None] = None
        self._serialLock = threading.Lock()
        self.killWithParentThread = True
        self._parentThread = threading.currentThread()

        self.idleCallback: Union[Callable[[], None], None] = None
        self.runningCallback: Union[Callable[[], None], None] = None
        self.errorCallback: Union[Callable[[ErrorCode], None], None] = None
        self.infoCallback: Union[Callable[[tuple, tuple, tuple, int], None], None] = None
        self.debugCallback: Union[Callable[[str], None], None] = None
        self.firmwareUpdateOKCallback: Union[Callable[[], None], None] = None
        self.firmwareUpdateFailedCallback: Union[Callable[[], None], None] = None
        self.readbackCallback: Union[Callable[[int, List[int]], None], None] = None
        self.singleAddressReadCallback: Union[Callable[[int], None], None] = None
        self.firwareUpdateStatusCallback: Union[Callable[[bool, int], None], None] = None

        self._latestFpgaRead: int = 0
        self._fpgaReadSemaphore = threading.Semaphore(0)
        self._deviceRunning: bool = False

        self._syncDiv: int = 1
        self._subcycles: int = 0
        self._triggerMode: TriggerMode = TriggerMode.Single
        self._vddio: float = 3.3

    def __del__(self):
        """Destructor - closes the device connection"""
        self.disconnect()

    def __enter__(self):
        """Enter - return instance."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit - disconnect from device."""
        if self.isConnected():
            self.disconnect()

    def _heartbeat(self):
        """Continually send a heartbeat message to the device until the connection is closed."""
        while (self._serialPort and self._serialPort.is_open and
               (self._parentThread.is_alive() or not self.killWithParentThread)):

            self._serialLock.acquire()
            if self.isConnected():
                self.writeToDevice(bytes([
                    Command.Heartbeat.value
                ]), False)
                self._serialLock.release()
                time.sleep(0.5)
            else:
                self._serialLock.release()
                break

    def _readback(self):
        """Continually read from the device and handle the status messages."""
        while (self.isConnected() and
               (self._parentThread.is_alive() or not self.killWithParentThread)):
            self._serialLock.acquire()
            try:
                if self.isConnected() and self._serialPort.in_waiting > 0:
                    statusbit = int.from_bytes(self._serialPort.read(1), byteorder='big')

                    if statusbit == Statusbit.Idle.value:
                        self._deviceRunning = False
                        if self.idleCallback is not None:
                            self.idleCallback()

                    elif statusbit == Statusbit.Running.value:
                        self._deviceRunning = True
                        if self.runningCallback is not None:
                            self.runningCallback()

                    elif statusbit == Statusbit.Error.value:
                        errorByte = self._serialPort.read(1)
                        error: ErrorCode = ErrorCode.FirmwareCorrupt

                        if errorByte == ErrorCode.FirmwareCorrupt.value:
                            error = ErrorCode.FirmwareCorrupt
                        elif errorByte == ErrorCode.FPGACorrupt.value:
                            error = ErrorCode.FPGACorrupt

                        if self.errorCallback is not None:
                            self.errorCallback(error)
                        else:
                            raise Exception("Device %s firmware is corrupt" %
                                            ("FPGA" if error == ErrorCode.FPGACorrupt else "microcontroller"))

                    elif statusbit == Statusbit.Info.value:
                        hwVer = tuple(self._serialPort.read(3))
                        ucVer = tuple(self._serialPort.read(3))
                        fpgaVer = tuple(self._serialPort.read(3))
                        flashId = int.from_bytes(self._serialPort.read(8), byteorder='big')

                        if self.infoCallback is not None:
                            self.infoCallback(hwVer, ucVer, fpgaVer, flashId)

                    elif statusbit == Statusbit.Debug.value:
                        string = self._serialPort.read_until(bytes([0]))[:-1].decode("ASCII")
                        if self.debugCallback is not None:
                            self.debugCallback(string)

                    elif statusbit == Statusbit.FirmwareUpdateOk.value:
                        if self.firmwareUpdateOKCallback is not None:
                            self.firmwareUpdateOKCallback()

                    elif statusbit == Statusbit.FirmwareUpdateFailed.value:
                        if self.firmwareUpdateFailedCallback is not None:
                            self.firmwareUpdateFailedCallback()

                    elif statusbit == Statusbit.Readback.value:
                        recorderId = int.from_bytes(self._serialPort.read(1), 'big')
                        numSamples = int.from_bytes(self._serialPort.read(2), 'big')
                        rawSamples = self._serialPort.read(4 * numSamples)
                        samples = []
                        for i in range(numSamples):
                            samples.append(int.from_bytes(rawSamples[i * 4:(i * 4) + 4], 'big'))

                        if self.readbackCallback is not None:
                            self.readbackCallback(recorderId, samples)

                    elif statusbit == Statusbit.SingleAddressRead.value:
                        data = int.from_bytes(self._serialPort.read(4), 'big')

                        if self.singleAddressReadCallback is not None:
                            self.singleAddressReadCallback(data)

                    elif statusbit == Statusbit.PinsStatus.value:
                        pinsA = int.from_bytes(self._serialPort.read(1), 'big')
                        pinsB = int.from_bytes(self._serialPort.read(1), 'big')
                        allPins = pinsA | (pinsB << 8)

                        for pinId in range(16):
                            self._allPins[pinId].inputLevel = 1 if (allPins & (1 << pinId)) else 0

                    elif statusbit == Statusbit.FirmwareUpdateStatus.value:
                        byte = int.from_bytes(self._serialPort.read(1), 'big')
                        isMicrocontroller: bool = (byte & 8) == 1
                        status: int = byte & 0xef

                        if self.firwareUpdateStatusCallback is not None:
                            self.firwareUpdateStatusCallback(isMicrocontroller, status)

                    else:
                        print("Unknown Status bit: %d" % statusbit)

            except serial.SerialException:
                pass

            except Exception as e:
                self._serialLock.release()
                raise e

            self._serialLock.release()

    def _connectToSpecifiedPort(self, portName: str, reset: bool, requestInfo: bool, configureGeneral: bool):
        """Try to connect to the specified port.

        :param str portName: The port to connect to
        :param bool reset: Reset the device after connection
        :param bool requestInfo: Request info from the device after connection
        :param bool configureGeneral: Configure general with the default values
        :return: Self
        :rtype: SmartWave
        :raises ConnectionRefusedError: If no connection to the device could be established"""
        try:
            self._serialLock.acquire()
            if self._serialPort is None:
                self._serialPort = serial.Serial(portName, baudrate=115200, exclusive=True, timeout=1)
            else:
                self._serialPort.port = portName

            self._serialLock.release()

        except (ConnectionRefusedError, serial.SerialException):
            self._serialLock.release()
            raise ConnectionRefusedError("Could not connect to serial port %s" % portName)

        if reset:
            self.reset()

        if configureGeneral:
            self.configGeneral()

        if requestInfo:
            self.requestInfo()

        self._heartbeatThread = threading.Thread(target=self._heartbeat)
        self._heartbeatThread.start()
        self._readingThread = threading.Thread(target=self._readback)
        self._readingThread.start()

        for entry in self.configEntries:
            entry.writeToDevice()
        return

    def scanAndConnect(self, reset: bool = True, requestInfo: bool = True, configureGeneral: bool = True):
        """Scan all serial ports on the PC and connect to a SmartWave device if one is found.

        :param bool reset: Reset the device after connection
        :param bool requestInfo: Request info from the device after connection
        :param bool configureGeneral: Configure general with the default values
        :return: Self
        :rtype: SmartWave
        :raises ConnectionRefusedError: If no suitable device is found"""

        # scans all ports and autoconnects to matching id
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if port.vid == SmartWave.VID and port.pid == SmartWave.PID:
                try:
                    self._connectToSpecifiedPort(port.device, reset, requestInfo, configureGeneral)
                    return self
                except ConnectionRefusedError:
                    # try another device
                    pass

        raise ConnectionRefusedError("Could not find a suitable device to connect to")

    def connect(self,
                portName: str = None,
                reset: bool = True,
                requestInfo: bool = True,
                configureGeneral: bool = True):
        """Try to connect to a SmartWave device at the specified port.

        :param str portName: The name of the port to connect to
        :param bool reset: Reset the device after connection
        :param bool requestInfo: Request info from the device after connection
        :param bool configureGeneral: Configure general with the default values
        :return: Self
        :rtype: SmartWave
        :raises ConnectionRefusedError: If no connection could be established with the specified port
        :raises AttributeError: If the device at the specified port is not a SmartWave device"""
        if portName is None:
            return self.scanAndConnect(reset)

        ports = serial.tools.list_ports.comports()
        for port in ports:
            if port.device == portName:
                if port.vid != SmartWave.VID or port.pid != SmartWave.PID:
                    raise AttributeError("The device at the specified port %s is not a SmartWave device" % port)

                self._connectToSpecifiedPort(portName, reset, requestInfo, configureGeneral)
                return self

        raise ConnectionRefusedError("Could not find specified serial port")

    def writeToDevice(self, data: bytes, acquireLock: bool = True):
        """Write bare data to the connected device.

        :param bytes data: the data to write
        :param bool acquireLock: Whether to acquire lock for serial resource.
            Setting this to False may have adverse side effects.
        :raises Exception: If the serial connection is not active"""

        if acquireLock:
            self._serialLock.acquire()
        if self._serialPort is None:
            if acquireLock:
                self._serialLock.release()
            raise Exception("Not connected to a device")

        self._serialPort.write(data)

        if acquireLock:
            self._serialLock.release()

    def isConnected(self) -> bool:
        """Return whether a device connection is currently active.

        :return: True if the device is connected, False otherwise"""
        return self._serialPort is not None and self._serialPort.isOpen()

    def disconnect(self):
        """Disconnect from the connected device."""
        self._serialLock.acquire()
        if self.isConnected():
            self._serialPort.flush()
            self._serialPort.close()

            self._serialLock.release()
            self._heartbeatThread.join()
            self._heartbeatThread = None
            self._readingThread.join()
            self._readingThread = None
            self._serialLock.acquire()
        self._serialPort = None
        self._serialLock.release()

    def trigger(self):
        """Start or Stop the current configuration on the connected device."""
        self.writeToDevice(bytes([
            Command.Trigger.value
        ]))

    def reset(self):
        """Reset the configuration of the connected device."""
        self.writeToDevice(bytes([
            Command.Reset.value
        ]))

    def configGeneral(self,
                      vddio: Union[float, None] = None,
                      triggerMode: Union[TriggerMode, None] = None):
        """Configure general information on the connected device.

        :param float vddio: The IO voltage of the connected device (accurate to 0.01V)
        :param TriggerMode triggerMode: The trigger mode of the output device
            (i.e. whether it runs once or continuously)

        :raises AttributeError: if vddio is not betweeen 1.8V and 5.0V"""

        if triggerMode is not None:
            self._triggerMode = triggerMode

        if vddio is not None:
            if vddio < 1.8:
                raise AttributeError("VDDIO needs to be above 1.8V")
            if vddio > 5:
                raise AttributeError("VDDIO needs to be below 5V")
            self._vddio = vddio

        vddioWord = int(self._vddio / 0.01)
        self.writeToDevice(bytes([
            Command.General.value,
            (self._syncDiv >> 8) & 0xff,
            self._syncDiv & 0xff,
            (self._subcycles >> 8) & 0xff,
            self._subcycles & 0xff,
            self._triggerMode.value,
            (vddioWord >> 8) & 0xff,
            vddioWord & 0xff
        ]))

    @property
    def vddio(self) -> float:
        """Get the current IO voltage of the connected device.

        :return: The current IO voltage of the connected device
        :rtype: float"""
        return self._vddio

    @vddio.setter
    def vddio(self, new_vddio: float):
        """Set the IO voltage of the connected device.

        :param float new_vddio: The new VDDIO of the device
        :raises ValueError: If the new VDDIO is not between 1.8V and 5.0V"""
        self.configGeneral(vddio=new_vddio)

    @property
    def triggerMode(self) -> TriggerMode:
        """Get the current trigger mode of the connected device.

        :return: The current trigger mode of the connected device
        :rtype: TriggerMode"""
        return self._triggerMode

    @triggerMode.setter
    def triggerMode(self, new_triggerMode: TriggerMode):
        """Set the current trigger mode of the connected device.

        :param TriggerMode new_triggerMode: The new triggermode"""
        self.configGeneral(triggerMode=new_triggerMode)

    def requestInfo(self):
        """Request the device information from the connected device."""
        self.writeToDevice(bytes([
            Command.Info.value
        ]))

    def getNextAvailableI2CDriver(self) -> I2CDriver:
        """Get the next available I2C Driver.

        :return: An I2C Driver, which has already been marked as in use
        :rtype: I2CDriver
        :raises Exception: If no more I2C Drivers are available on the device"""
        if len(self._availableI2CDrivers):
            return self._availableI2CDrivers.pop(0)
        else:
            raise Exception("No more I2C Drivers available on this device")

    def getNextAvailableSPIDriver(self) -> SPIDriver:
        """Get the next available SPI Driver.

        :return: An SPI Driver, which has already been marked as in use
        :rtype: SPIDriver
        :raises Exception: If no more SPI Drivers are available on the device"""
        if len(self._availableSPIDrivers):
            return self._availableSPIDrivers.pop(0)
        else:
            raise Exception("No more SPI Drivers available on this device")

    def returnI2CDriver(self, driver: I2CDriver) -> int:
        """Return an I2C Driver to the list of available I2C Drivers.

        :param I2CDriver driver: The I2C driver to return
        :return: The new number of available I2C Drivers
        :rtype: int"""
        self._availableI2CDrivers.append(driver)
        return len(self._availableI2CDrivers)

    def returnSPIDriver(self, driver: SPIDriver) -> int:
        """Return an SPI Driver to the list of available SPI Drivers.

        :param SPIDriver driver: The SPI driver to return
        :return: The new number of available SPI drivers
        :rtype: int"""
        self._availableSPIDrivers.append(driver)
        return len(self._availableSPIDrivers)

    def getNextAvailablePin(self) -> Pin:
        """Get the next available Pin.

        :return: A Pin, which has already been marked as in use
        :rtype: Pin
        :raises Exception: If no more Pins are available on the device"""
        if len(self._availablePins):
            return self._availablePins.pop(0)
        else:
            raise Exception("No more pins available on this device")

    def getPin(self, name: str) -> Pin:
        """Get a pin by its name.

        :param str name: The pin's name
        :return: The specified pin, which has already been marked as in use
        :rtype: Pin
        :raises AttributeError: If the pin name does not exist on the device
        :raises Exception: If the pin is already in use"""

        bank = name[:1]
        numberStr = name[1:]

        if bank not in ["A", "B"] or not numberStr.isdigit():
            raise AttributeError("Invalid Pin name")

        number = int(numberStr)

        if number not in [1, 2, 3, 4, 7, 8, 9, 10]:
            raise AttributeError("Invalid Pin number")

        foundIndex = -1

        for i in range(len(self._availablePins)):
            pin = self._availablePins[i]
            if pin.getBank() == bank and pin.getNumber() == number:
                foundIndex = i
                break

        if foundIndex == -1:
            raise Exception("The specified pin is already in use")

        return self._availablePins.pop(foundIndex)

    def returnPin(self, pin: Pin) -> int:
        """Return a Pin to the list of available pins.

        :param Pin pin: The pin to return
        :return: The new number of available pins
        :rtype: int"""
        self._availablePins.append(pin)
        return len(self._availablePins)

    def getNextAvailableStimulus(self) -> Stimulus:
        """Get the next available stimulus.

        :return: A Stimulus, which has already been marked as in use
        :rtype: Stimulus
        :raises Exception: If no more Stimuli are available on the device"""
        if len(self._availablePins):
            return self._availableStimuli.pop(0)
        else:
            raise Exception("No more stimuli available on this device")

    def returnStimulus(self, stimulus: Stimulus) -> int:
        """Return a stimulus to the list of available stimuli.

        :param Stimulus stimulus: The stimulus to return
        :return: The new number of available stimuli
        :rtype: int"""
        self._availableStimuli.append(stimulus)
        return len(self._availableStimuli)

    def createI2CConfig(self, sdaPinName: Optional[str] = None, sclPinName: Optional[str] = None,
                        clockSpeed: Optional[int] = None) -> I2CConfig:
        """Create an I2C Configuration object.

        :param str sdaPinName: The name of the pin to use for SDA
        :param str sclPinName: The name of the pin to use for SCL
        :param int clockSpeed: The I2C clock speed in Hz
        :return: An I2C Configuration with the specified settings
        :rtype: I2CConfig"""
        sdaPin = self.getPin(sdaPinName) if sdaPinName else None
        sclPin = self.getPin(sclPinName) if sclPinName else None

        config: I2CConfig = I2CConfig(self, sdaPin, sclPin, clockSpeed)
        self.configEntries.append(config)

        return config

    def createSPIConfig(self,
                        sclkPinName: Optional[str] = None,
                        mosiPinName: Optional[str] = None,
                        misoPinName: Optional[str] = None,
                        ssPinName: Optional[str] = None,
                        clockSpeed: Optional[int] = None,
                        bitWidth: Optional[int] = None,
                        bitNumbering: Optional[Literal["MSB", "LSB"]] = None,
                        cspol: Optional[Literal[0, 1]] = None,
                        cpol: Optional[Literal[0, 1]] = None,
                        cphase: Optional[Literal[0, 1]] = None):
        """Create an SPI Configuration object.

        :param str sclkPinName: The name of the pin to use for SCLK
        :param str mosiPinName: The name of the pin to use for MOSI
        :param str misoPinName: The name of the pin to use for MISO
        :param str ssPinName: The name of the pin to use for SS
        :param int clockSpeed: The transmission clock speed in Hz
        :param int bitWidth: The bit width of the SPI transmissions
        :param Literal["MSB", "LSB"] bitNumbering: Whether to transmit MSB-first or LSB-first
        :param Literal[0, 1] cspol: The polarity of the chipselect pin
        :param Literal[0, 1] cpol: The polarity of the clock pin
        :param Literal[0, 1] cphase: The phase of the clock
        :return: An SPI Configuration with the specified settings
        :rtype: SPIConfig
        """
        sclkPin = self.getPin(sclkPinName) if sclkPinName else None
        misoPin = self.getPin(misoPinName) if misoPinName else None
        mosiPin = self.getPin(mosiPinName) if mosiPinName else None
        ssPin = self.getPin(ssPinName) if ssPinName else None

        config: SPIConfig = SPIConfig(self,
                                      sclkPin,
                                      mosiPin,
                                      misoPin,
                                      ssPin,
                                      clockSpeed,
                                      bitWidth,
                                      bitNumbering,
                                      cspol,
                                      cpol,
                                      cphase)
        self.configEntries.append(config)

        return config
    
    def createGPIO(self,
                   pin_name: Optional[str] = None,
                   name: Optional[str] = None,
                   level: Optional[Literal[0, 1]] = None,
                   pullup: Optional[bool] = None,
                   output_type: Optional[PinOutputType] = None,
                   input_level_callback: Optional[Callable[[Literal[0, 1]], None]] = None) -> GPIO:
        """Create a GPIO configuration object.

        :param str pin_name: The name of the pin to use, eg "A1"
        :param str name: The name of the GPIO pin, as displayed on the device, eg "GPIO"
        :param Literal[0, 1] level: The initial level of the pin
        :param bool pullup: Whether to enable a pullup resistor on the pin
        :param PinOutputType output_type: The output type of the pin
        :param Callable[[Literal[0, 1]], None] input_level_callback: A callable to be run whenever the input level of the pin is changed.

        :return: A GPIO configuration object
        :rtype: GPIO"""
        pin = self.getPin(pin_name) if pin_name else self.getNextAvailablePin()

        args: Dict[str, any] = {}

        if name is not None:
            args["name"] = name

        if level is not None:
            args["level"] = level

        if pullup is not None:
            args["pullup"] = pullup

        if output_type is not None:
            args["output_type"] = output_type

        if input_level_callback is not None:
            args["input_level_callback"] = input_level_callback

        gpio: GPIO = GPIO(self, pin, **args)
        return gpio

    def removeConfig(self, config: Config):
        """Remove a config from the device.

        :param Config config: the config to remove
        :raises AttributeError: If the config is not found"""
        index = self.configEntries.index(config)

        if index == -1:
            raise AttributeError("No such config found")

        config.delete()
        del self.configEntries[index]

    def writeFPGARegister(self, address: int, value: int):
        """Write directly to a register on the SmartWave's FPGA.

        :param int address: The address to write to
        :param int value: The value to write"""
        self.writeToDevice(bytes([Command.FpgaWrite.value]) +
                           address.to_bytes(3, 'big') +
                           value.to_bytes(4, 'big'))

    def _fpgaReadCallbackHandler(self, value: int):
        """Handle the result of an FPGA register read."""
        self._latestFpgaRead = value
        self._fpgaReadSemaphore.release()

    def readFPGARegister(self, address: int, blocking: bool = True) -> Union[int, None]:
        """Read directly from a register on the SmartWave's FPGA.

        :param int address: The address to read from
        :param bool blocking: If true, wait for the response from the connected device
        :return: If blocking == True, return the content of the specified register. Else return None.
        :rtype: Union[int, None]
        :raises Exception: If the blocking mode is requested and another callback for a register read operation
        is already registered"""
        if blocking:
            if self.singleAddressReadCallback is not None:
                raise Exception("Cannot configure a blocking read operation because there is already a single-address"
                                " read callback registered on the device")

            self.singleAddressReadCallback = self._fpgaReadCallbackHandler

        self.writeToDevice(bytes([Command.FpgaRead.value]) +
                           address.to_bytes(3, 'big'))

        if blocking:
            # wait for read value
            self._fpgaReadSemaphore.acquire()

            # release callback
            self.singleAddressReadCallback = None

            return self._latestFpgaRead

        return None

    def updateFirmware(self, firmwarePath: Optional[str] = None):
        """Update the microcontroller firmware with a given firmware, or to the newest version.

        This also checks the firmware file for plausibility and calculates the checksum.

        :param Optional[str] firmwarePath: The path to the new firmware. If unspecified, upload newest
            packaged firmware.
        :raises FileNotFoundError: If the firmware file could not be found
        :raises Exception: If the firmware file is incompatible with the bootloader
        :raises Exception: If the firmware size is incompatible with the bootloader"""
        f = open(firmwarePath if firmwarePath else
                 os.path.join(os.path.dirname(os.path.abspath(__file__)), "newest_firmware.bin"), "rb")
        f_check = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "SBL_sample.bin"), "rb")

        # check if given file is cropped (webgui) or raw (from arduino IDE)
        f_size = f.seek(0, os.SEEK_END)
        f_check_size = f_check.seek(0, os.SEEK_END)

        if f_size == f_check_size:
            cropped = False
        elif f_size > self.FirmwareEnd - self.FirmwareStart:
            cropped = True
        else:
            raise Exception("The size of the given file suggests that it is not a valid firmware")

        if not cropped:
            f.seek(self.SBLStart)
            f_check.seek(self.SBLStart)

            # check if SBL was changed
            while f.tell() < self.FirmwareStart:
                if f.read(1) != f_check.read(1):
                    # the given firmware has a different SBL; will not be compatible
                    raise Exception("The given firmware is not compatible with the current bootloader on the device!")

            # check if firmware chunk is big enough
            f.seek(self.FirmwareEnd)
            for i in range(16):
                if f.read(1) != b'\x00':
                    raise Exception("The firmware size seems to be incompatible with the device!")

        dataLen = self.FirmwareEnd - self.FirmwareStart
        commands = bytes([
            Command.FirmwareUpdate.value,
            0x1b,
            (dataLen >> 24) & 0xff,
            (dataLen >> 16) & 0xff,
            (dataLen >> 8) & 0xff,
            dataLen & 0xff
        ])

        f_start = self.FirmwareStart if not cropped else 0
        f_end = self.FirmwareEnd if not cropped else dataLen

        f.seek(f_start)
        checksum = 0xC0DEF19E
        while f.tell() <= f_end:
            checksum += int.from_bytes(f.read(4), "little")
        checksum %= 0x100000000

        f.seek(f_start)
        data = f.read(dataLen)

        checksumArray = int.to_bytes(checksum, 4, "big")

        f.close()
        f_check.close()

        self.writeToDevice(commands + data + checksumArray)

    def updateFPGABitstream(self, bitstreamPath: Optional[str] = None):
        """Update the FPGA bitstream with a given bitstream, or to the newest version.

        Also checks the bitstream file for plausibility and calculates the checksum.

        :param Optional[str] bitstreamPath: The path to the bitstream. If unspecified,
            upload newest packaged bitstream.
        :raises FileNotFoundError: If the bitstream file could not be found
        :raises Exception: If the bitstream file is of the wrong size"""

        f = open(bitstreamPath if bitstreamPath else
                 os.path.join(os.path.dirname(os.path.abspath(__file__)), "newest_fpga_bitstream.bin"), "rb")

        # size check
        f.seek(0, os.SEEK_END)
        fileSize = f.tell()
        if fileSize != 0x21728c:
            raise Exception(
                "The bitstream seems to be of the wrong size: 0x%x. Please check for correctness." % fileSize)

        # checksum
        f.seek(self.FPGABitstreamStart)
        checksum = 0xC0DEF19E
        while f.tell() + 4 <= fileSize and f.tell() + 4 <= self.FPGABitstreamEnd:
            num = int.from_bytes(f.read(4), "big")
            checksum += num
            checksum %= 0x100000000

        f.seek(self.FPGABitstreamStart)

        commands = bytes([
            Command.FpgaUpdate.value,
            0x1c,
            (fileSize >> 24) & 0xff,
            (fileSize >> 16) & 0xff,
            (fileSize >> 8) & 0xff,
            fileSize & 0xff
        ])
        data = f.read()
        checksumArray = checksum.to_bytes(4, "big")
        f.close()

        self.writeToDevice(commands + data + checksumArray)

import serial
import serial.tools.list_ports
import threading
import time

from typing import List, Union, Callable

from SmartWaveAPI.configitems import Pin, I2CDriver, Stimulus, Config
from SmartWaveAPI.configitems.i2cconfig import I2CConfig
from SmartWaveAPI.definitions import Command, Statusbit, ErrorCode


class SmartWave:
    """An instance of a SmartWave device. Keeps track of all available resources."""
    VID: int = 0x2341
    PID: int = 0x8071
    FPGAClockSpeed: int = 100e6

    def __init__(self):
        """Create a new SmartWave instance."""
        self._serialPort = None

        self._availableI2CDrivers = [
            I2CDriver(self, 0),
            I2CDriver(self, 1),
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

        self.configEntries: List[Config] = []

        self._heartbeatThread = threading.Thread(target=self._heartbeat)
        self._readingThread = threading.Thread(target=self._readback)
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
        self.pinsStatusCallback: Union[Callable[[int, int], None], None] = None
        self.firwareUpdateStatusCallback: Union[Callable[[bool, int], None], None] = None

        self._latestFpgaRead: int = 0
        self._fpgaReadSemaphore = threading.Semaphore(0)

    def _heartbeat(self):
        """Continually send a heartbeat message to the device until the connection is closed."""
        while (self._serialPort and self._serialPort.is_open and
               (self._parentThread.is_alive() or not self.killWithParentThread)):
            self.writeToDevice(bytes([
                Command.Heartbeat.value
            ]))
            time.sleep(0.5)

    def _readback(self):
        """Continually read from the device and handle the status messages."""
        while (self._serialPort and self._serialPort.is_open and
               (self._parentThread.is_alive() or not self.killWithParentThread)):
            try:
                if self._serialPort and self._serialPort.is_open and self._serialPort.in_waiting > 0:
                    self._serialLock.acquire()
                    statusbit = int.from_bytes(self._serialPort.read(1), byteorder='big')

                    if statusbit == Statusbit.Idle.value:
                        if self.idleCallback is not None:
                            self.idleCallback()

                    elif statusbit == Statusbit.Running.value:
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

                        if self.pinsStatusCallback is not None:
                            self.pinsStatusCallback(pinsA, pinsB)

                    elif statusbit == Statusbit.FirmwareUpdateStatus.value:
                        byte = int.from_bytes(self._serialPort.read(1), 'big')
                        isMicrocontroller: bool = (byte & 8) == 1
                        status: int = status & 0xef

                        if self.firwareUpdateStatusCallback is not None:
                            self.firwareUpdateStatusCallback(isMicrocontroller, status)


                    else:
                        print("Unknown Status bit: %d" % statusbit)

                    self._serialLock.release()


            except serial.SerialException:
                pass

    def _connectToSpecifiedPort(self, portName: str, reset: bool, requestInfo: bool):
        """Try to connect to the specified port.

        :param str portName: The port to connect to
        :param bool reset: Reset the device after connection
        :param bool requestInfo: Request info from the device after connection
        :return: Self
        :rtype: SmartWave
        :raises ConnectionRefusedError: If no connection to the device could be established
        """
        try:
            if self._serialPort is None:
                self._serialPort = serial.Serial(portName, baudrate=115200)
            else:
                self._serialPort.port = portName

            if reset:
                self.reset()

            if requestInfo:
                self.requestInfo()

            self._heartbeatThread.start()
            self._readingThread.start()

            return

        except ConnectionRefusedError as e:
            raise ConnectionRefusedError("Could not connect to serial port %s" % portName)

    def scanAndConnect(self, reset: bool = True, requestInfo: bool = True):
        """Scan all serial ports on the PC and connect to a SmartWave device if one is found.

        :param bool reset: Reset the device after connection
        :param bool requestInfo: Request info from the device after connection
        :return: Self
        :rtype: SmartWave
        :raises ConnectionRefusedError: If no suitable device is found"""

        # scans all ports and autoconnects to matching id
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if port.vid == SmartWave.VID and port.pid == SmartWave.PID:
                try:
                    self._connectToSpecifiedPort(port.device, reset, requestInfo)
                    return self
                except ConnectionRefusedError as e:
                    # try another device
                    pass

        raise ConnectionRefusedError("Could not find a suitable device to connect to")

    def connect(self, portName: str = None, reset: bool = True, requestInfo: bool = True):
        """Try to connect to a SmartWave device at the specified port.

        :param str portName: The name of the port to connect to
        param bool reset: Reset the device after connection
        param bool requestInfo: Request info from the device after connection
        :return: Self
        :rtype: SmartWave
        :raises ConnectionRefusedError: If no connection could be established with the specified port
        raises AttributeError: If the device at the specified port is not a SmartWave device"""
        if portName is None:
            self.scanAndConnect(reset)
            return

        ports = serial.tools.list_ports.comports()
        for port in ports:
            if port.device == portName:
                if port.vid != SmartWave.VID or port.pid != SmartWave.PID:
                    raise AttributeError("The device at the specified port %s is not a SmartWave device" % port)

                self._connectToSpecifiedPort(portName, reset, requestInfo)
                return self

        raise ConnectionRefusedError("Could not find specified serial port")

    def writeToDevice(self, data: bytes):
        """Write bare data to the connected device.

        :param bytes data: the data to write
        :raises Exception: If the serial connection is not active"""
        if (self._serialPort is None):
            raise Exception("Not connected to a device")

        # print(list(data))
        self._serialLock.acquire()
        self._serialPort.write(data)
        self._serialLock.release()

    def isConnected(self) -> bool:
        """Return whether a device connection is currently active.

        :return: True if the device is connected, False otherwise"""
        return self._serialPort is not None

    def disconnect(self):
        """Disconnect from the connected device."""
        self._serialPort.close()
        self._serialPort = None
        self._heartbeatThread.join()
        self._readingThread.join()

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

        if not bank in ["A", "B"] or not numberStr.isdigit():
            raise AttributeError("Invalid Pin name")

        number = int(numberStr)

        if not number in [1, 2, 3, 4, 7, 8, 9, 10]:
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

    def getNextAvailableStimulus(self) -> Stimulus:
        """Get the next available stimulus.

        :return: A Stimulus, which has already been marked as in use
        :rtype: Stimulus
        :raises Exception: If no more Stimuli are available on the device"""
        if len(self._availablePins):
            return self._availableStimuli.pop(0)
        else:
            raise Exception("No more stimuli available on this device")

    def createI2CConfig(self, sdaPinName: Union[str, None] = None, sclPinName: Union[str, None] = None,
                        clockSpeed: Union[int, None] = None) -> I2CConfig:
        """Create an I2C Configuration object.

        :param str sdaPinName: The name of the pin to use for SDA
        :param str sclPinName: The name of the pin to use for SCL
        :param int clockSpeed: The I2C clock speed in Hz
        :return: An I2C Configuration with the specified settings
        :rtype: I2CConfig
        """
        sdaPin = self.getPin(sdaPinName) if sdaPinName else None
        sclPin = self.getPin(sclPinName) if sclPinName else None

        config: I2CConfig = I2CConfig(self, sdaPin, sclPin, clockSpeed)
        self.configEntries.append(config)

        return config

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
        :raises Exception: If the blocking mode is requested and another callback for a register read operation is already registered"""
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
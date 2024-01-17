import serial
import serial.tools.list_ports
import threading
import time

from typing import List

from SmartWaveAPI.configitems import Pin, I2CDriver, Stimulus, Config
from SmartWaveAPI.configitems.i2cconfig import I2CConfig
from SmartWaveAPI.definitions import I2CTransaction, Command, Statusbit, ErrorCodes


class SmartWave:

    VID: int = 0x2341
    PID: int = 0x8071
    FPGAClockSpeed: int = 100e6

    def __init__(self):
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


    def _heartbeat(self):
        while self._serialPort and self._serialPort.is_open:
            self.writeToDevice(bytes([
                Command.Heartbeat.value
            ]))
            time.sleep(0.5)

    def _readback(self):
        while self._serialPort and self._serialPort.is_open:
            try:
                if self._serialPort and self._serialPort.is_open and self._serialPort.in_waiting > 0:
                    self._serialLock.acquire()
                    statusbit = int.from_bytes(self._serialPort.read(1), byteorder='big')

                    if statusbit == Statusbit.Idle.value:
                        print("Idle")

                    elif statusbit == Statusbit.Running.value:
                        print("Running")

                    elif statusbit == Statusbit.Error.value:
                        error = self._serialPort.read(1)
                        if error == ErrorCodes.FirmwareCorrupt.value:
                            print("Firmware corrupt")
                        elif error == ErrorCodes.FPGACorrupt.value:
                            print("FPGA corrupt")

                    elif statusbit == Statusbit.Info.value:
                        hwVer = tuple(self._serialPort.read(3))
                        ucVer = tuple(self._serialPort.read(3))
                        fpgaVer = tuple(self._serialPort.read(3))
                        flashId = int.from_bytes(self._serialPort.read(8), byteorder='big')

                        print('Info:\n'
                              'HW version: %s\n'
                              'UC version: %s\n'
                              'FPGA version: %s\n'
                              'Flash id: %s' % (hwVer, ucVer, fpgaVer, flashId))

                    elif statusbit == Statusbit.Debug.value:
                        string = self._serialPort.read_until(bytes([0]))[:-1].decode("ASCII")
                        print(string)

                    elif statusbit == Statusbit.FirmwareUpdateOk.value:
                        print("Firmware update OK")

                    elif statusbit == Statusbit.FirmwareUpdateFailed.value:
                        print("Firmware update Failed")

                    elif statusbit == Statusbit.Readback.value:
                        recorderId = int.from_bytes(self._serialPort.read(1))
                        numSamples = int.from_bytes(self._serialPort.read(2), byteorder='big')
                        samples = self._serialPort.read(4 * numSamples)
                        print("Recorder Readback", samples)

                    elif statusbit == Statusbit.SingleAddressRead.value:
                        data = int.from_bytes(self._serialPort.read(4), byteorder='big')
                        print("Single Address Read", data)

                    elif statusbit == Statusbit.PinsStatus.value:
                        pinsA = int.from_bytes(self._serialPort.read(1), 'big')
                        pinsB = int.from_bytes(self._serialPort.read(1), 'big')
                        print("PinsStatus", pinsA, pinsB)

                    elif statusbit == Statusbit.FirmwareUpdateStatus.value:
                        status = int.from_bytes(self._serialPort.read(1), 'big')
                        print("%s update Status: %s" % (
                            "FPGA" if status & 8 == 0 else "Microcontroller",
                            ('%d%%' % (status & 0xeff)) if status < 127 else "finished"
                        ))


                    else:
                        print("Unknown Status bit: %d" % statusbit)

                    self._serialLock.release()


            except serial.SerialException:
                pass


    def _connectToSpecifiedPort(self, portName: str, reset: bool, requestInfo: bool):
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

        except Exception as e:
            raise ConnectionRefusedError("Could not connect to serial port %s" % portName)


    def scanAndConnect(self, reset: bool = True, requestInfo: bool = True):
        # scans all ports and autoconnects to matching id
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if port.vid == SmartWave.VID and port.pid == SmartWave.PID:
                try:
                    self._connectToSpecifiedPort(port.device, reset, requestInfo)
                    return
                except ConnectionRefusedError as e:
                    # try another device
                    pass

        raise Exception("Could not find a suitable device to connect to")

    def connect(self, portName: str = None, reset: bool = True, requestInfo: bool = True):
        if portName is None:
            self.scanAndConnect(reset)
            return

        ports = serial.tools.list_ports.comports()
        for port in ports:
            if port.device == portName:
                if port.vid != SmartWave.VID or port.pid != SmartWave.PID:
                    raise Exception("The device at the specified port %s is not a SmartWaveAPI device" % port)

                self._connectToSpecifiedPort(portName, reset, requestInfo)

        raise Exception("Could not find specified serial port")

    def writeToDevice(self, data: bytes):
        if (self._serialPort is None):
            raise Exception("Not connected to a device")

        # print(list(data))
        self._serialLock.acquire()
        self._serialPort.write(data)
        self._serialLock.release()

    def isConnected(self) -> bool:
        return self._serialPort is not None

    def disconnect(self):
        self._serialPort.close()
        self._serialPort = None
        self._heartbeatThread.join()
        self._readingThread.join()

    def trigger(self):
        self.writeToDevice(bytes([
            Command.Trigger.value
       ]))

    def reset(self):
        self.writeToDevice(bytes([
            Command.Reset.value
        ]))

    def requestInfo(self):
        self.writeToDevice(bytes([
            Command.Info.value
        ]))

    def getNextAvailableI2CDriver(self) -> I2CDriver:
        return self._availableI2CDrivers.pop(0)

    def getNextAvailablePin(self) -> Pin:
        return self._availablePins.pop(0)

    def getNextAvailableStimulus(self) -> Stimulus:
        return self._availableStimuli.pop(0)

    def createI2CConfig(self) -> I2CConfig:
        config: I2CConfig = I2CConfig(self)
        self.configEntries.append(config)

        return config







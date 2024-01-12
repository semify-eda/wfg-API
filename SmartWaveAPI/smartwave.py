import serial
import serial.tools.list_ports

from typing import List

from SmartWaveAPI.configitems import Pin, I2CDriver, Stimulus, ConfigEntry
from SmartWaveAPI.definitions import I2CTransaction


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

        self.configEntries: List[ConfigEntry] = []

    def scanAndConnect(self):
        # scans all ports and autoconnects to matching id
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if port.vid == SmartWave.VID and port.pid == SmartWave.PID:
                try:
                    if self._serialPort is None:
                        self._serialPort = serial.Serial(port.device, baudrate=115200)
                    else:
                        self._serialPort.port = port.device

                    return
                except Exception as e:
                    # try another device
                    pass

        raise Exception("Could not find a suitable device to connect to")

    def connect(self, portName: str = None):
        if portName is None:
            self.scanAndConnect()
            return

        ports = serial.tools.list_ports.comports()
        for port in ports:
            if port.device == portName:
                if port.vid != SmartWave.VID or port.pid != SmartWave.PID:
                    raise Exception("The device at the specified port %s is not a SmartWaveAPI device" % port)

                try:
                    if self._serialPort is None:
                        self._serialPort = serial.Serial(portName, baudrate=115200)
                    else:
                        self._serialPort.port = portName

                    return

                except Exception as e:
                    raise Exception("Could not connect to serial port %s" % port)

        raise Exception("Could not find specified serial port")

    def writeToDevice(self, data: bytes):
        if (self._serialPort is None):
            raise Exception("Not connected to a device")

        print(data)
        self._serialPort.write(data)

    def setupI2C(self, transactions: List[I2CTransaction]):
        driver = self._availableI2CDrivers.pop(0)
        driver.pins['SCL'] = self._availablePins.pop(0)
        driver.pins['SDA'] = self._availablePins.pop(0)
        stimulus = self._availableStimuli.pop(0)

        stimulus.sampleBitWidth = 32
        stimulus.samples = driver.generateSamples(transactions)

        self.configEntries.append(
            ConfigEntry(self, driver, stimulus)
        )

        self.configEntries[-1].writeToDevice()







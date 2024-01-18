from SmartWaveAPI.definitions import TriggerMode, Command
from typing import List


class Stimulus(object):
    stimulusType: int = 0

    def __init__(self, device, id: int):
        self._device = device
        self._id = id
        self.sampleBitWidth: int = 8
        self.triggerMode: TriggerMode = TriggerMode.Single
        self.samples: List[int] = [0xa, 0xb]

    def writeToDevice(self):
        shiftedSamples = []

        for sample in self.samples:
            bitShift = self.sampleBitWidth - 8
            while bitShift >= 0:
                shiftedSamples.append((sample >> bitShift) & 0xff)

                bitShift = bitShift - 8

        self._device.writeToDevice(bytes([
            Command.Stimulus.value,
            self.stimulusType, # only arbitrary stimulus supported right now
            self._id,
            self.sampleBitWidth,
            0 if self.triggerMode == TriggerMode.Toggle else 1,
            (len(self.samples) >> 8) & 0xff,
            len(self.samples) & 0xff
        ] + shiftedSamples))

    def getId(self):
        return self._id
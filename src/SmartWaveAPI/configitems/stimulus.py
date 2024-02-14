from SmartWaveAPI.definitions import TriggerMode, Command, StimulusType
from typing import List


class Stimulus(object):
    """A hardware stimulus on the SmartWave device"""
    stimulusType: int = StimulusType.Arbitrary.value

    def __init__(self, device, id: int):
        """Create a new Stimulus instance. Only to be called in SmartWave.__init__() function.

        :param SmartWave device: the SmartWave device this stimulus belongs to
        :param int id: the ID of this stimulus"""
        self._device = device
        self._id = id
        self.sampleBitWidth: int = 8
        self.triggerMode: TriggerMode = TriggerMode.Single
        self.samples: List[int] = [0xa, 0xb]

    def __del__(self) -> None:
        """Destructor - return all resources to the device."""
        self.delete()

    def writeToDevice(self):
        """Write the configuration parameters of this pin to the device."""
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

    def getId(self) -> int:
        """Get the ID of this stimulus.

        :return: the ID of this stimulus
        :rtype: int"""
        return self._id

    def delete(self):
        self._device.returnStimulus(self)
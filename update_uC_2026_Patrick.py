# Update the SmartWave microcontroller to the packaged firmware
# (src/SmartWaveAPI/newest_firmware.bin).
#
# NOTE: updateFirmware() classifies its input by FILE SIZE:
#   - size == SBL_sample.bin (253704)      -> raw wfg-arduino.ino.bin (IDE export)
#   - size  > firmware-window (0xF200)     -> cropped webgui image
# NEVER feed it wfg-arduino.ino.with_bootloader.bin: it is misclassified as
# "cropped" and its first 62 KB (bootloader+SBL code!) get flashed into the
# app region -> "Device microcontroller firmware is corrupt".
# To flash a custom build, pass the path to robust_flash.py instead.
import time
from SmartWaveAPI import SmartWave

def main():
    sw = SmartWave()
    sw.connect()
    sw.firmwareUpdateStatusCallback = \
        lambda isUc, s: print("%s update: %d%%" % ("uC" if isUc else "FPGA", s))
    sw.updateFirmware()  # packaged newest_firmware.bin
    print("waiting 60 s for the device to flash + restart - do NOT unplug")
    time.sleep(60)
    print("done - power-cycle, then run check_version.py")

if __name__ == "__main__":
    main()

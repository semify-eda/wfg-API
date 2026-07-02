# Flash a locally-built wfg-arduino firmware to the SmartWave MCU.
# (Fills in for the referenced-but-missing robust_flash.py.)
#
# Pass the RAW IDE export  wfg-arduino.ino.bin  -- it must be 253704 bytes (same
# size as SBL_sample.bin). updateFirmware() classifies the input by FILE SIZE:
#   size == 253704  -> raw IDE export, flashed to the app region (what we want)
#   size != 253704  -> treated as a cropped webgui image -> CORRUPTS the app region
# So NEVER pass wfg-arduino.ino.with_bootloader.bin (wrong size).
#
# Flashing goes over the existing serial link to the on-MCU serial bootloader --
# the device does NOT re-enumerate, so this works fine over USB/IP from WSL.
import os
import sys
import time
from SmartWaveAPI import SmartWave

if len(sys.argv) != 2:
    sys.exit("usage: python flash_uC_firmware.py <path-to-wfg-arduino.ino.bin>")

path = sys.argv[1]
size = os.path.getsize(path)
print("flashing %s (%d bytes)" % (path, size))
if size != 253704:
    print("WARNING: expected 253704 bytes (raw IDE export); %d bytes will be treated"
          " as a cropped image and may CORRUPT the app region." % size)
    if input("continue anyway? [y/N] ").strip().lower() != "y":
        sys.exit("aborted")

sw = SmartWave()
sw.connect()
sw.firmwareUpdateStatusCallback = \
    lambda isUc, s: print("%s update: %d%%" % ("uC" if isUc else "FPGA", s))
sw.updateFirmware(path)
print("waiting 60 s for the device to flash + restart -- do NOT unplug")
time.sleep(60)
print("done -- power-cycle, then run check_version.py")

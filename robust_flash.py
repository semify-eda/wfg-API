import sys, time
from SmartWaveAPI import SmartWave

sw = SmartWave()
sw.connect()
sw.firmwareUpdateStatusCallback = lambda isUc, s: print(f"{'uC' if isUc else 'FPGA'} update: {s}%")
try:
    sw.updateFirmware(sys.argv[1])
except Exception as e:
    print("update call raised:", e)
print("waiting 60 s - do NOT unplug")
time.sleep(60)
print("done - now power-cycle the SmartWave")

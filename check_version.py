from SmartWaveAPI import SmartWave
import time

with SmartWave().connect() as sw:
    sw.infoCallback = lambda hw, uc, fpga, flashId: print(
        f"HW {hw}  uC {uc}  FPGA {fpga}  flash 0x{flashId:x}")
    sw.requestInfo()
    time.sleep(2)

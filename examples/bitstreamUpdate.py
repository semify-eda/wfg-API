from SmartWaveAPI import SmartWave
import time

def main():
    with SmartWave().connect() as sw:
        sw.firwareUpdateStatusCallback = lambda isUc, status : print("%s update status: %d%%" % ("Microcontroller" if isUc else "FPGA", status))
        sw.infoCallback = lambda hw, uc, fpga, flashId: print("Hardware version: %s\nMicrocontroller version: %s\nFPGA version: %s\nFlash ID: 0x%x" % (hw, uc, fpga, flashId))
        # sw.updateFPGABitstream()


if __name__ == "__main__":
    main()
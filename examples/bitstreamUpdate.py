from SmartWaveAPI import SmartWave
import time

def main():
    with SmartWave().connect() as sw:
        sw.firwareUpdateStatusCallback = lambda isUc, status : print("%s update status: %d%%" % ("Microcontroller" if isUc else "FPGA", status))
        sw.infoCallback = lambda hw, uc, fpga, flashId: print("Hardware version: %s\nMicrocontroller version: %s\nFPGA version: %s\nFlash ID: 0x%x" % (hw, uc, fpga, flashId))
        # sw.updateFPGABitstream("../../rtl-design-amd-fpga/vivado/my_bitstream_for_SPIx1_config.bin")
        # time.sleep(1)
        # sw.requestInfo()
        # time.sleep(1)
        # sw.updateFirmware("../../wfg-arduino/build/arduino.samd.mkrzero/wfg-arduino.ino.bin")
        # sw.updateFirmware("C:/Users/chris/Documents/wfg/webgui/public/firmware/uc0812.bin")


if __name__ == "__main__":
    main()
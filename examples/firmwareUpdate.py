from SmartWaveAPI import SmartWave

def main():
    with SmartWave().connect() as sw:
        sw.firwareUpdateStatusCallback = lambda isUc, status : print(isUc, status)
        sw.updateFPGABitstream("../../rtl-design-amd-fpga/vivado/my_bitstream_for_SPIx1_config.bin")
        sw.updateFirmware("../../wfg-arduino/build/arduino.samd.mkrzero/wfg-arduino.ino.bin")


if __name__ == "__main__":
    main()
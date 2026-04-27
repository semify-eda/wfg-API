from SmartWaveAPI import SmartWave

def main():
    with SmartWave().connect() as sw:
        sw.firmwareUpdateStatusCallback = lambda isUc, status : print("%s update status: %d%%" % ("Microcontroller" if isUc else "FPGA", status))
        sw.updateFirmware("C:\\Users\\siebp\\Documents\\projects\\TRISTAN\\wfg-arduino\\build\\arduino.samd.mkrzero\\wfg-arduino.ino.with_bootloader.bin")

if __name__ == "__main__":
    main()

from SmartWaveAPI import SmartWave

def main():
    with SmartWave().connect() as sw:
        sw.firmwareUpdateStatusCallback = lambda isUc, status : print("%s update status: %d%%" % ("Microcontroller" if isUc else "FPGA", status))
        sw.updateFirmware()


if __name__ == "__main__":
    main()
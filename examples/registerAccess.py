from SmartWaveAPI import SmartWave


def main():


    sw = SmartWave()
    sw.connect()

    sw.debugCallback = lambda x: print(x)

    sw.writeFPGARegister(0x20000, 1234)
    print(sw.readFPGARegister(0x20000))

if __name__ == "__main__":
    main()
from SmartWaveAPI import SmartWave
import time

def main():
    with SmartWave().connect() as sw:
        with sw.createSPIConfig(bitWidth=16, misoPinName="A3", mosiPinName="A2", clockSpeed=2e6, bitNumbering="MSB") as spi:
            data = spi.write([0x8f00])

            for dat in data:
                print("%x" % dat)


if __name__ == "__main__":
    main()
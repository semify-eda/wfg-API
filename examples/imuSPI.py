from SmartWaveAPI import SmartWave
import time

cycle_time = 0.001
def main():
    with (SmartWave().connect() as sw):
        sw.createSPIConfig(misoPinName="B1", mosiPinName="B2", ssPinName="B3", sclkPinName="B4")
        with sw.createSPIConfig(
                bitWidth=16,
                misoPinName="A1",
                mosiPinName="A2",
                sclkPinName="A3",
                ssPinName="A4",
                clockSpeed=2e6,
                bitNumbering="MSB") as spi:
            whoami = spi.write([0x8f00])[0]
            print(whoami)

            spi.write([0x1010])

            start = time.time()
            next_time = start + cycle_time
            for i in range(1000):
                while (time.time() < next_time):
                    pass
                val = spi.write([0xaa00])[0]
                val = val if val < 0x8000 else val - 0x10000
                print(val)
                next_time += cycle_time

            spi.cpol = 1
            spi.cphase = 1

            for i in range(1000):
                while (time.time() < next_time):
                    pass
                val = spi.write([0xaa00])[0]
                val = val if val < 0x8000 else val - 0x10000
                print(val)
                next_time += cycle_time

            spi.cphase = 0

            for i in range(1000):
                while (time.time() < next_time):
                    pass
                val = spi.write([0xaa00])[0]
                val = val if val < 0x8000 else val - 0x10000
                print(val)
                next_time += cycle_time


            print(time.time() - start)


if __name__ == "__main__":
    main()
from SmartWaveAPI import SmartWave
import time

cycle_time = 0.001
def main():
    with (SmartWave().connect() as sw):
        # sw.createSPIConfig(miso_pin_name="B1", mosi_pin_name="B2", cs_pin_name="B3", sclk_pin_name="B4")
        with sw.createSPIConfig(
                bit_width=16,
                miso_pin_name="A1",
                mosi_pin_name="A4",
                sclk_pin_name="A3",
                cs_pin_name="A2",
                clock_speed=int(2e6),
                bit_numbering="MSB",
                cs_inactive_time=5,
        ) as spi:
            whoami = spi.write([0x8f00])[0]
            print(whoami)
            # input()
            spi.write([0x1010])

            start = time.time()
            next_time = start + cycle_time
            while True:
                # while (time.time() < next_time):
                #     pass
                val = spi.write([0xaa00])[0]
                val = val if val < 0x8000 else val - 0x10000
                print(val)
                next_time += cycle_time
                # input()

            print(time.time() - start)


if __name__ == "__main__":
    main()
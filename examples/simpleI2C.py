from SmartWaveAPI import SmartWave
from SmartWaveAPI.definitions import I2CWrite, I2CRead, TriggerMode
import time

def main():

    start = time.time()
    with SmartWave().connect() as sw:
        sw.createI2CConfig("A1", "A2")
        sw.triggerMode = TriggerMode.Toggle
        with sw.createI2CConfig("A8", "A7") as i2c:
            # sw.debugCallback = lambda x: print(x)

            i2c.write(0x20, [0xaa, 0x55])
            print("first: ", i2c.read(0x20, 2))
            i2c.write(0x20, [0x55, 0xaa])
            print("second: ", i2c.read(0x20, 2))
            # i2c.write(0x20, [0xff, 0xff])
            # print("thirst: ", i2c.read(0x20, 2))

        for i in range(180, 400):
            sw.vddio = float(i) / 100
            time.sleep(0.1)
        sw.vddio = 4
        with sw.createI2CConfig("A8", "A7") as i2c:
            # sw.debugCallback = lambda x: print(x)

            i2c.write(0x20, [0xaa, 0x55])
            print("first: ", i2c.read(0x20, 2))
            i2c.write(0x20, [0x55, 0xaa])
            print("second: ", i2c.read(0x20, 2))
            i2c.write(0x20, [0xff, 0xff])
            print("thirst: ", i2c.read(0x20, 2))

        sw.vddio = 5

        with sw.createI2CConfig("A9", "A7") as i2c:
            # sw.debugCallback = lambda x: print(x)

            i2c.write(0x20, [0xaa, 0x55])
            print("first: ", i2c.read(0x20, 2))
            i2c.write(0x20, [0x55, 0xaa])
            print("second: ", i2c.read(0x20, 2))
            i2c.write(0x20, [0xff, 0xff])
            print("thirst: ", i2c.read(0x20, 2))

        sw.vddio = 3.3
        with sw.createI2CConfig("A8", "A7") as i2c:
            # sw.debugCallback = lambda x: print(x)

            i2c.write(0x20, [0xaa, 0x55])
            print("first: ", i2c.read(0x20, 2))
            i2c.write(0x20, [0x55, 0xaa])
            print("second: ", i2c.read(0x20, 2))
            i2c.write(0x20, [0xff, 0xff])
            print("thirst: ", i2c.read(0x20, 2))

    print("elapsed time: ", time.time() - start)


if __name__ == "__main__":
    main()

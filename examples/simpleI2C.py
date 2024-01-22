from SmartWaveAPI import SmartWave
from SmartWaveAPI.definitions import I2CWrite, I2CRead
import time

def main():

    start = time.time()
    with SmartWave() as sw:
            with sw.createI2CConfig("A2", "A1") as i2c:
                sw.debugCallback = lambda x: print(x)
                sw.connect()

                i2c.write(0x20, [0xaa, 0x55])
                print("first: ", i2c.read(0x20, 2))
                i2c.write(0x20, [0x55, 0xaa])
                print("second: ", i2c.read(0x20, 2))
                i2c.write(0x20, [0xff, 0xff])
                print("thirst: ", i2c.read(0x20, 2))

                sw.disconnect()
                print("disconnected")
                # SmartWave().connect("COM19")
                # SmartWave().connect("COM10")
                # SmartWave().connect()
                print("other connect")
                sw.connect()

                i2c.write(0x20, [0xaa, 0x55])
                print("first: ", i2c.read(0x20, 2))
                i2c.write(0x20, [0x55, 0xaa])
                print("second: ", i2c.read(0x20, 2))
                i2c.write(0x20, [0xff, 0xff])
                print("thirst: ", i2c.read(0x20, 2))
    print("elapsed time: ", time.time() - start)


if __name__ == "__main__":
    main()

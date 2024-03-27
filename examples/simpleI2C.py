from SmartWaveAPI import SmartWave
from SmartWaveAPI.definitions import I2CWrite, I2CRead, TriggerMode
import time

def main():

    with SmartWave().connect() as sw:
        sw.vddio = 3.3
        with sw.createI2CConfig("A2", "A1") as i2c:
            # sw.debugCallback = lambda x: print(x)

            i2c.write(0x20, [0xaa, 0x55])
            print("first: ", i2c.read(0x20, 2))
            i2c.write(0x20, [0x55, 0xaa])
            print("second: ", i2c.read(0x20, 2))
            i2c.write(0x20, [0xff, 0xff])
            print("thirst: ", i2c.read(0x20, 2))





if __name__ == "__main__":
    main()

from SmartWaveAPI import SmartWave
from SmartWaveAPI.definitions import I2CWrite, I2CRead
import time

def main():
    sw = SmartWave()
    sw.connect()

    i2c = sw.createI2CConfig("A2", "A1")
    sw.readbackCallback = lambda x, y: print(x, y)

    i2c.write(0x20, [0xaa, 0x55])
    print("first: ", i2c.read(0x20, 2, False))
    i2c.write(0x20, [0x55, 0xaa])
    print("second: ", i2c.read(0x20, 2, False))
    i2c.write(0x20, [0xff, 0xff])
    print("thirst: ", i2c.read(0x20, 2, False))


    time.sleep(1)
    sw.disconnect()



if __name__ == "__main__":
    main()
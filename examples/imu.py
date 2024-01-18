from SmartWaveAPI import SmartWave
from SmartWaveAPI.definitions import I2CWrite, I2CRead
import time

def main():
    sw = SmartWave()
    sw.connect()

    i2c = sw.createI2CConfig("A2", "A1", 200e3)

    print(i2c.readRegister(0b1101010, [0x0f], 1))
    sw.disconnect()



if __name__ == "__main__":
    main()
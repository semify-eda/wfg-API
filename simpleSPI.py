from SmartWaveAPI import SmartWave
from SmartWaveAPI.definitions import I2CTransaction
import time

def main():
    sw = SmartWave()
    sw.connect()
    sw.setupI2C([
        I2CTransaction(0x20, False, [1, 2, 3]),
    ])

    for i in range(3):
        time.sleep(1)
        sw.trigger()


    sw.disconnect()



if __name__ == "__main__":
    main()
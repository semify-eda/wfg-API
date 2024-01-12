from SmartWaveAPI import SmartWave
from SmartWaveAPI.definitions import I2CTransaction

def main():
    sw = SmartWave()
    sw.connect()
    sw.setupI2C([
        I2CTransaction(0x20, False, [1, 2, 3]),
    ])



if __name__ == "__main__":
    main()
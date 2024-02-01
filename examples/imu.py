from SmartWaveAPI import SmartWave
import time

def main():
    sw = SmartWave()
    sw.connect()

    i2c = sw.createI2CConfig("A2", "A1", 200e3)
    devId = 0b1101010

    i2c.writeRegister(
        devId,
        0x10.to_bytes(1, 'big'),
        0b00010000.to_bytes(1, 'big')
    )
    print(i2c.readRegister(0b1101010, [0x0f], 1))

    # sw.readbackCallback = lambda _, x : print("-" * (int(int.from_bytes(x, 'little', signed=True) / 300) + 150))
    # ret1 = i2c.readRegister(0b1101010, [0x28], 2, False)

    start = time.time()
    for i in range(20000):
        # sw.trigger()
        # time.sleep(0.005)
        ret1 = i2c.readRegister(0b1101010, [0x2A], 2)
        # ret2 = i2c.readRegister(0b1101010, [0x2A], 2)
        # ret3 = i2c.readRegister(0b1101010, [0x2C], 2, False)
        print("-" * (int(int.from_bytes(ret1, 'little', signed=True) / 300) + 150))
        # print("-" * (int(int.from_bytes(ret2, 'little', signed=True) / 300) + 150))
        # print("-" * (int(int.from_bytes(ret3, 'little', signed=True) / 300) + 150))

    print(time.time() - start)
    sw.disconnect()



if __name__ == "__main__":
    main()
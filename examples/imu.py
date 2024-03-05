from SmartWaveAPI import SmartWave

def main():
    with SmartWave().connect() as sw:
        with sw.createI2CConfig("A2", "A1", 200e3) as i2c:
            devId = 0b1101010

            i2c.writeRegister(
                devId,
                0x10.to_bytes(1, 'big'),
                0b00010000.to_bytes(1, 'big')
            )
            print(i2c.readRegister(0b1101010, [0x0f], 1))


            while True:
                ret1 = i2c.readRegister(0b1101010, [0x2A], 2)
                print("-" * (int(int.from_bytes(ret1, 'little', signed=True) / 300) + 150))


if __name__ == "__main__":
    main()
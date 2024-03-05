from SmartWaveAPI import SmartWave

sw = SmartWave().connect()
i2c = sw.createI2CConfig()
i2c.write(0x20, bytes([0xaa, 0xbb]))
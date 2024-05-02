from SmartWaveAPI import SmartWave

sw = SmartWave().connect()
sw.debugCallback = lambda x: print(x)
i2c = sw.createI2CConfig(sda_pin_name="A4", scl_pin_name="A3")
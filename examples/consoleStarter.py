from SmartWaveAPI import SmartWave

sw = SmartWave().connect()
i2c = sw.createI2CConfig(sda_pin_name="A2", scl_pin_name="A3")
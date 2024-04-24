from SmartWaveAPI import SmartWave

sw = SmartWave().connect()
# sw.debugCallback = lambda x: print(x)
# i2c = sw.createI2CConfig(sda_pin_name="A2", scl_pin_name="A3")
spi = sw.createSPIConfig(miso_pin_name="B1", mosi_pin_name="B2", cs_pin_name="B3", sclk_pin_name="B4", clock_speed=100e3)
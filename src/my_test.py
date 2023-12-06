from api import *
import time

smartWave_init()

smartWave_reset()

time.sleep(1)
#smartWave_status()
print('')
#smartWave_write_address(0x20000, 0x12345679)

#time.sleep(1)

#print(hex(smartWave_read_address(0x20000)))


i2c_id = setup_i2c(0xa1, 0xa2)

print('')

i2c_transaction(i2c_id, device_select = 0x12, datalen = 1, data = [0], read_not_write = 1)

smartWave_close()

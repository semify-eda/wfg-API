from api import *
import time


I2C0_ADDR = 0x84000
MEM_STIM0 = 0x20000
MEM_REC0 = 0x28000



def print_mem():
  print('', flush=True)
  print('memory of stim0', flush=True)
  for i in range(10):
    print(hex(smartWave_read_address(MEM_STIM0 + i*4)), flush=True)

  print('memory of rec0', flush=True)
  for i in range(10):
    print(hex(smartWave_read_address(MEM_REC0 + i*4)), flush=True)






smartWave_init()

smartWave_reset()

#time.sleep(1)
#smartWave_status()
print('', flush=True)
#smartWave_write_address(0x20000, 0x12345679)

#time.sleep(1)
print_mem()

print('', flush=True)
print('setup_i2c', flush=True)


i2c_id = setup_i2c(0xa2, 0xa1)


print_mem()

print('', flush=True)
print('i2c_transaction', flush=True)

i2c_transaction(i2c_id, device_select = 0x20, datalen = 2, data = [0xee, 0xee], read_not_write = 0)
#i2c_transaction(i2c_id, device_select = 0x20, datalen = 2, data = [0xff, 0xff], read_not_write = 0)
#print(hex(smartWave_read_address(0x46038)))

print_mem()

print('', flush=True)
print('smartWave_close', flush=True)

smartWave_close()

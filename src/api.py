# .py

"""This module allows communication with a semify smartWave."""


#__all__ = ['smartWave_init', 'smartWave_close']
__author__ = "semify GmbH"
__version__ = "0.0.1"



import serial
import serial.tools.list_ports
import asyncio
import serial_asyncio

import time

__SmartWave__ = None


COMMAND_RESET = b'\x00'
COMMAND_TRIGGER = b'\x01'
COMMAND_STOP = b'\x02'
COMMAND_STIMULUS = b'\x03'
COMMAND_DRIVER = b'\x04'
COMMAND_PIN = b'\x05'
COMMAND_STIMULUSDRIVERMATRIX = b'\x06'
COMMAND_DRIVERPINMATRIX = b'\x07'
COMMAND_GENERAL = b'\x08'
COMMAND_INFO = b'\x09'
COMMAND_HEARTBEAT = b'\x0A'
COMMAND_FIRMWAREUPDATE = b'\x0B'
COMMAND_FPGAUPDATE = b'\x0C'
COMMAND_FPGAWRITE = b'\x0D'
COMMAND_FPGAREAD = b'\x0E'

STIMULUSTYPE_ARBITRARY = b'\x00'

DRIVERTYPE_SPI = b'\x00'
DRIVERTYPE_I2C = b'\x01'
DRIVERTYPE_I2S = b'\x02'
DRIVERTYPE_UART = b'\x03'
DRIVERTYPE_CONST = b'\x04'
DRIVERTYPE_NODRIVER = b'\xFF'

PINOUTPUTTYPE_DISABLE = b'\x00'
PINOUTPUTTYPE_PUSHPULL = b'\x01'
PINOUTPUTTYPE_OPENDRAIN = b'\x02'

TRIGGERMODE_SINGLE = b'\x00'
TRIGGERMODE_FULL = b'\x01'
TRIGGERMODE_TOGGLE = b'\x02'

STATUSBIT_IDLE = b'\x01'
STATUSBIT_RUNNING = b'\x02'
STATUSBIT_ERROR = b'\x03'
STATUSBIT_INFO = b'\x04'
STATUSBIT_DEBUG = b'\x05'
STATUSBIT_FIRMWAREUPDATEOK = b'\x06'
STATUSBIT_FIRMWAREUPDATEFAILED = b'\x07'
STATUSBIT_READBACK = b'\x08'
STATUSBIT_SINGLEADDRESSREAD = b'\x09'

DRIVER_TYPE_SPI = 0x00
DRIVER_TYPE_I2C = 0x01
DRIVER_TYPE_I2S = 0x02
DRIVER_TYPE_UART = 0x03


PIN_DISABLED = 0
PIN_LOW = 1
PIN_HIGH = 2


PIN_PUSH_PULL = 0
PIN_OPEN_DRAIN = 1



#available hardware
__num_stim_mem__ = 4
__num_drive_i2c__ = 2
__num_drive_spi__ = 2
__num_drive_uart__ = 2
__num_pins__ = 16

#tracking of in use hardware

__stim__ = []
__i2c__ = []
__spi__ = []
__uart__ = []
__pins__ = []


class Stim_and_Rec:
  in_use = False


class Driver:
  in_use = False
  stim_and_rec_assigned = -1


class Pin:
  in_use = False
  vpin = PIN_DISABLED
  mode = PIN_PUSH_PULL


def _init_ds():
  global __stim__
  global __i2c__
  global __spi__
  global __uart__
  global __pins__

  for i in range(__num_stim_mem__):
    entry = Stim_and_Rec()
    entry.id = i
    __stim__.append(entry)

  for i in range(__num_drive_i2c__):
    entry = Driver()
    entry.id = i
    __i2c__.append(entry)

  for i in range(__num_drive_spi__):
    entry = Driver()
    entry.id = i
    __spi__.append(entry)

  for i in range(__num_drive_uart__):
    entry = Driver()
    entry.id = i
    __uart__.append(entry)

  for i in range(__num_pins__):
    entry = Pin()
    entry.id = i
    __pins__.append(entry)




def get_free_i2c():
  for i in range(__num_drive_i2c__):
    if not __i2c__[i].in_use:
      return i


def get_free_stim():
  for i in range(__num_stim_mem__):
    if not __stim__[i].in_use:
      return i



def setup_i2c(sclpin, sdapin):
  i2c_id = get_free_i2c()
  stim_id = get_free_stim()

  __i2c__[i2c_id].in_use = True
  __i2c__[i2c_id].stim_and_rec_assigned = stim_id
  __stim__[stim_id].in_use = True

  #TODO check if pins are free
  smartWave_pin_config(sclpin, pullup = 1)
  #time.sleep(1)
  smartWave_pin_config(sdapin, pullup = 1)
  #time.sleep(1)
  smartWave_dpmatrix(DRIVER_TYPE_I2C, i2c_id, 0, sclpin, 0x3456, 3, name = 'scl')
  #time.sleep(1)
  smartWave_dpmatrix(DRIVER_TYPE_I2C, i2c_id, 1, sdapin, 0x3456, 3, name = 'sda')
  #time.sleep(1)
  smartWave_drive_i2c(i2c_id, cdiv = 100)
  #time.sleep(1)
  smartWave_sdmatrix(0, stim_id, DRIVER_TYPE_I2C, i2c_id)
  #time.sleep(1)
  smartWave_genconfig(syncdiv = 1, subcycles = 0, triggermode = 0, vddio = 330)
  #time.sleep(1)


  return i2c_id

def i2c_transaction(i2c_id, device_select, datalen, data, read_not_write):
  if not read_not_write and  len(data) != datalen:
    raise RuntimeError("i2c write, but datalen does not match provided data")

  stim_id = __i2c__[i2c_id].stim_and_rec_assigned

  encoded_data = add_i2c_command_frame(datalen, device_select, data, read_not_write)

  print(encoded_data, flush=True)
  smartWave_stim_mem(id = stim_id, bitwidth = 32, repetition = 1, sample_count = (datalen+1), samples = encoded_data)


  __SmartWave__.reset_input_buffer()

  print(' ', flush=True)
  #time.sleep(1)
  smartWave_trigger()

  #print(' ', flush=True)
  #time.sleep(1)
  #smartWave_stop()

  __SmartWave__.flush()
  print(' ', flush=True)


  #for _ in range(20):
  #  print(__SmartWave__.read(1), flush=True)


def add_i2c_command_frame(datalen, device_select, data, read_not_write):
  command_frame = 0
  command_frame += datalen & 0xff
  command_frame += 1<<16 #use device select in frame
  command_frame += (device_select & 0xff) << 17
  command_frame |= (read_not_write & 0x1) << 25

  retval = []
  retval.append(command_frame.to_bytes(4, 'big'))

  for entry in data:
    retval.append(entry.to_bytes(4, 'big'))

  return retval




def smartWave_init():
  global __SmartWave__
  global __pins__
  if __SmartWave__ is not None:
    raise RuntimeError("There is already a smartWave connected")
    return

  portlist = list(serial.tools.list_ports.comports())
  i = 0
  for port in portlist:
    if port[2].startswith("USB VID:PID=2341:8071"):
      __SmartWave__ = serial.Serial(portlist[i][0], 115200, timeout=1)
      #print("matched")
      #__SmartWave__.write('test'.encode('ascii'))
      break
    i += 1

  if __SmartWave__ is None:
    raise RuntimeError("No smartWave found")
    return

  _init_ds()
  return



def smartWave_close():
  global __SmartWave__
  if __SmartWave__ is None:
    raise RuntimeError("There is no smartWave connected")
    return

  __SmartWave__.close()
  __SmartWave__ = None



def _smartWave_apply_command(send_bytes = [b'\x00']):
  if __SmartWave__ is None:
    raise RuntimeError("There is no smartWave connected")
    return

  #print('sending', flush=True)
  for byte in send_bytes:
    #print(byte, flush=True)
    #print(bytes(byte).hex(), flush=True)
    __SmartWave__.write(byte)
  __SmartWave__.flush()


def smartWave_reset():
  _smartWave_apply_command([COMMAND_RESET])

def smartWave_trigger():
  _smartWave_apply_command([COMMAND_TRIGGER])

def smartWave_stop():
  _smartWave_apply_command([COMMAND_STOP])
  #TODO evaluate response and read rest of data
  #after data is read see if another recorder sends data?

'''
STATUSBIT_READBACK

'''


def smartWave_stim_mem(id = 0, bitwidth = 32, repetition = 1, sample_count = 1, samples = [b'\x00']):
  command = [COMMAND_STIMULUS, b'\x00']
  command.append(id.to_bytes(1, 'big'))
  command.append(bitwidth.to_bytes(1, 'big'))

  if repetition:
    command.append(b'\x01')
  else:
    command.append(b'\x00')

  command.append(sample_count.to_bytes(2, 'big'))

  response = _smartWave_apply_command(command + samples)


def smartWave_drive_spi(id = 0, enable = 1, bitwidth = 32, msbfirst = 1, cpol = 0, cpha = 0, cdiv = 1):
  command = [COMMAND_DRIVER]
  command.append(DRIVERTYPE_SPI)
  command.append(id.to_bytes(1, 'big'))
  command.append(enable.to_bytes(1, 'big'))
  command.append(msbfirst.to_bytes(1, 'big'))
  command.append(cpol.to_bytes(1, 'big'))
  command.append(cpha.to_bytes(1, 'big'))
  command.append(cdiv.to_bytes(2, 'big'))

  response = _smartWave_apply_command(command)


def smartWave_drive_i2c(id = 0, enable = 1, cdiv = 1):
  command = [COMMAND_DRIVER]
  command.append(DRIVERTYPE_I2C)
  command.append(id.to_bytes(1, 'big'))
  command.append(enable.to_bytes(1, 'big'))
  command.append(cdiv.to_bytes(2, 'big'))

  response = _smartWave_apply_command(command)

def smartWave_drive_i2s(id = 0, enable = 1, cdiv = 1):
  command = [COMMAND_DRIVER]
  command.append(DRIVERTYPE_I2S)
  command.append(id.to_bytes(1, 'big'))
  command.append(enable.to_bytes(1, 'big'))
  command.append(cdiv.to_bytes(2, 'big'))

  response = _smartWave_apply_command(command)


def smartWave_drive_uart(id = 0, enable = 1, bitwidth = 32, cdiv = 1):
  command = [COMMAND_DRIVER]
  command.append(id.to_bytes(1, 'big'))
  command.append(DRIVERTYPE_I2C)
  command.append(enable.to_bytes(1, 'big'))
  command.append(cdiv.to_bytes(2, 'big'))
  command.append(bitwidth.to_bytes(1, 'big'))

  response = _smartWave_apply_command(command)


def smartWave_pin_config(id = 0, pullup = 0):
  command = [COMMAND_PIN]
  command.append(id.to_bytes(1, 'big'))
  command.append(b'\x01')
  command.append(b'\x01')
  command.append(pullup.to_bytes(1, 'big'))

  response = _smartWave_apply_command(command)


#connects stim AND rec to driver
def smartWave_sdmatrix(stimtype = 0xff, stimid = 0, drivertype = 0, driverid = 0):
  command = [COMMAND_STIMULUSDRIVERMATRIX]
  command.append(stimtype.to_bytes(1, 'big'))
  command.append(stimid.to_bytes(1, 'big'))
  command.append(drivertype.to_bytes(1, 'big'))
  command.append(driverid.to_bytes(1, 'big'))

  response = _smartWave_apply_command(command)


def smartWave_dpmatrix(dtype, did, vpin, pin, color, namelen, name = 'noname'):
  command = [COMMAND_DRIVERPINMATRIX]
  command.append(dtype.to_bytes(1, 'big'))
  command.append(did.to_bytes(1, 'big'))
  command.append(vpin.to_bytes(1, 'big'))
  command.append(pin.to_bytes(1, 'big'))
  command.append(color.to_bytes(2, 'big'))
  command.append(namelen.to_bytes(1, 'big'))
  command.append(name.encode('ascii'))

  response = _smartWave_apply_command(command)


def smartWave_genconfig(syncdiv, subcycles, triggermode, vddio):
  command = [COMMAND_GENERAL]
  command.append(syncdiv.to_bytes(2, 'big'))
  command.append(subcycles.to_bytes(2, 'big'))
  command.append(triggermode.to_bytes(1, 'big'))
  command.append(vddio.to_bytes(2, 'big'))

  response = _smartWave_apply_command(command)



def smartWave_status():
  _smartWave_apply_command([COMMAND_INFO])

  response = __SmartWave__.read(18)
  print("status response:", flush=True)
  print(bytes(response).hex(), flush=True)



def smartWave_write_address(address, data):
  command = [COMMAND_FPGAWRITE]
  command.append(address.to_bytes(3, 'big'))
  command.append(data.to_bytes(4, 'big'))
  response = _smartWave_apply_command(command)


def smartWave_read_address(address):
  command = [COMMAND_FPGAREAD]
  command.append(address.to_bytes(3, 'big'))

  __SmartWave__.reset_input_buffer()

  _smartWave_apply_command(command)

  response = __SmartWave__.read(5)
  intresponse = int.from_bytes(response, byteorder='big')

  return intresponse & 0xffffffff








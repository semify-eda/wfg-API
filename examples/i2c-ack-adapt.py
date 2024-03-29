from SmartWaveAPI import SmartWave
from SmartWaveAPI.definitions import I2CWrite, I2CRead, TriggerMode
import time


from fpga_reg import FPGA_Reg



def set_register(sw, address, data):
    print("set register: addr: %x, data: %x" % (address, data))
    sw.writeFPGARegister(address, data)


def set_register_8bit(sw, address, data):
    print("set register: addr: %x, data: %x" % (address, data))
    sw.writeFPGARegister(address, data)


def read_register(sw, address):
    data = sw.readFPGARegister(address)
    print("read register: addr: %x, data: %x" % (address, data))
    return data


def configure_core(sw, en=1, sync_count=1, subcycle_count=1):
  localenv = FPGA_Reg.registers["wfg_core_top"]
  addr = localenv["CFG"]["addr"]
  sync_shift = localenv["CFG"]["SYNC"]["LSB"]
  subcycle_shift = localenv["CFG"]["SUBCYCLE"]["LSB"]
  set_register(sw, addr, (sync_count << sync_shift) | (subcycle_count << subcycle_shift))
  addr = localenv["CTRL"]["addr"]
  en_shift = localenv["CTRL"]["EN"]["LSB"]
  set_register_8bit(sw, addr, en << en_shift)

def configure_mem(sw, nbr, data_array):
  addr = FPGA_Reg.memory | (nbr << 13)
  for dat in data_array:
    set_register(sw, addr, dat)
    addr = addr + 4

def configure_subcore(sw, en=1, sync_count=1, subcycle_count=1):
  set_register(sw, 0x42004, (sync_count << 0) | (subcycle_count << 8))
  set_register_8bit(sw, 0x42000, en)

def configure_interconnect(sw, spi0=0xff, spi1=0xff, i2c0=0xff, uart0=0xff,recorder0=0xff,recorder1=0xff, pat=0xff):
  localenv = FPGA_Reg.registers["wfg_interconnect_top"]
  if spi0 != 0xff:
    addr = localenv["wfg_drive_spi_top_0_select_0"]["addr"]
    set_register_8bit(sw, addr, spi0)
  if spi1 != 0xff:
    addr = localenv["wfg_drive_spi_top_1_select_0"]["addr"]
    set_register_8bit(sw, addr, spi1)
  if i2c0 != 0xff:
    addr = localenv["wfg_drive_i2c_top_0_select_0"]["addr"]
    set_register_8bit(sw, addr, i2c0)
  if pat != 0xff:
    addr = localenv["wfg_drive_pat_top_0_select_0"]["addr"]
    set_register_8bit(sw, addr, pat)
  if uart0 != 0xff:
    addr = localenv["wfg_drive_uart_top_0_select_0"]["addr"]
    set_register_8bit(sw, addr, uart0)
  if recorder0 != 0xff:
    addr = localenv["wfg_record_mem_top_0_select_0"]["addr"]
    set_register_8bit(sw, addr, recorder0)
  if recorder1 != 0xff:
    addr = localenv["wfg_record_mem_top_1_select_0"]["addr"]
    set_register_8bit(sw, addr, recorder1)


def configure_stim_mem(sw, localenv, en=1, count=0, start=0x0000, end=0x00FF, step=0x04, gain=0x0001, ier=0):
  cnt_shift = localenv["CFG"]["CNT"]["LSB"]
  addr = localenv["CFG"]["addr"]
  set_register(sw, addr, count << cnt_shift)

  start_shift = localenv["START"]["VAL"]["LSB"]
  addr = localenv["START"]["addr"]
  set_register(sw, addr, start << start_shift)

  end_shift = localenv["STOP"]["VAL"]["LSB"]
  addr = localenv["STOP"]["addr"]
  set_register(sw, addr, end << end_shift)

  step_shift = localenv["STEP"]["VAL"]["LSB"]
  addr = localenv["STEP"]["addr"]
  set_register(sw, addr, step << step_shift)

  gain_shift = localenv["GAIN"]["VAL"]["LSB"]
  addr = localenv["GAIN"]["addr"]
  set_register(sw, addr, gain << gain_shift)

  addr = localenv["IER"]["addr"]
  set_register(sw, addr, 0)

  en_shift = localenv["CTRL"]["EN"]["LSB"]
  addr = localenv["CTRL"]["addr"]
  set_register_8bit(sw, addr, en << en_shift)

def configure_stim_mem_0(sw, en=1, count=0, start=0x0000, end=0x00FF, step=0x04, gain=0x0001):
  localenv = FPGA_Reg.registers["wfg_stim_mem_top_0"]
  configure_stim_mem(sw, localenv, en, count, start, end, step, gain)

def configure_stim_mem_1(sw, en=1, start=0x0000, end=0x00FF, step=0x04, gain=0x0001, count=0):
  localenv = FPGA_Reg.registers["wfg_stim_mem_top_1"]
  configure_stim_mem(sw, localenv, en, count, start, end, step, gain)

def configure_stim_mem_2(sw, en=1, start=0x0000, end=0x00FF, step=0x04, gain=0x0001, count=0):
  localenv = FPGA_Reg.registers["wfg_stim_mem_top_2"]
  configure_stim_mem(sw, localenv, en, count, start, end, step, gain)

def configure_stim_mem_3(sw, en=1, start=0x0000, end=0x00FF, step=0x04, gain=0x0001, count=0):
  localenv = FPGA_Reg.registers["wfg_stim_mem_top_3"]
  configure_stim_mem(sw, localenv, en, count, start, end, step, gain)


def reenable_stim_mem_0(sw, start=0x0000, end=0x00FF):
  localenv = FPGA_Reg.registers["wfg_stim_mem_top_0"]

  start_shift = localenv["START"]["VAL"]["LSB"]
  addr = localenv["START"]["addr"]
  set_register(sw, addr, start << start_shift)

  end_shift = localenv["STOP"]["VAL"]["LSB"]
  addr = localenv["STOP"]["addr"]
  set_register(sw, addr, end << end_shift)

  en_shift = localenv["CTRL"]["EN"]["LSB"]
  addr = localenv["CTRL"]["addr"]
  set_register_8bit(sw, addr, 1 << en_shift)


def clear_interrupt_stim_mem_0(sw):
  localenv = FPGA_Reg.registers["wfg_stim_mem_top_0"]
  addr = localenv["ICR"]["addr"]
  set_register(sw, addr, 0x3)



def configure_record_mem(sw, localenv, en=1, start=0x0000, end=0x0fff, step=0x04, count=0):
  cnt_shift = localenv["CFG"]["CNT"]["LSB"]
  addr = localenv["CFG"]["addr"]
  set_register(sw, addr, count << cnt_shift)

  start_shift = localenv["START"]["VAL"]["LSB"]
  addr = localenv["START"]["addr"]
  set_register(sw, addr, start << start_shift)

  end_shift = localenv["STOP"]["VAL"]["LSB"]
  addr = localenv["STOP"]["addr"]
  set_register(sw, addr, end << end_shift)

  step_shift = localenv["STEP"]["VAL"]["LSB"]
  addr = localenv["STEP"]["addr"]
  set_register(sw, addr, step << step_shift)

  en_shift = localenv["CTRL"]["EN"]["LSB"]
  addr = localenv["CTRL"]["addr"]
  set_register_8bit(sw, addr, en << en_shift)


def configure_record_mem_0(sw, en=1, start=0x0000, end=0x0fff, step=0x04, count=0):
  localenv = FPGA_Reg.registers["wfg_record_mem_top_0"]
  configure_record_mem(sw, localenv, en=en, count=count, start=start, end=end, step=step)


def configure_record_mem_1(sw, en=1, start=0x0000, end=0x0fff, step=0x04, count=0):
  localenv = FPGA_Reg.registers["wfg_record_mem_top_1"]
  configure_record_mem(sw, localenv, en=en, count=count, start=start, end=end, step=step)


def clear_interrupt_record_mem_1(sw):
  localenv = FPGA_Reg.registers["wfg_record_mem_top_0"]
  addr = localenv["ICR"]["addr"]
  set_register(sw, addr, 0x3)


def configure_drive_spi_0(sw, en=1, core_sel=0, div=3, cpol=0, cpha=0, lsbfirst=0,sspol=0, io_delay_comp=0, txlen=8):
  localenv = FPGA_Reg.registers["wfg_drive_spi_top_0"]

  addr = localenv["CFG"]["addr"]
  cpol_shift = localenv["CFG"]["CPOL"]["LSB"]
  cpha_shift = localenv["CFG"]["CPHA"]["LSB"]
  lsbfirst_shift = localenv["CFG"]["LSBFIRST"]["LSB"]
  sspol_shift = localenv["CFG"]["SSPOL"]["LSB"]
  core_sel_shift = localenv["CFG"]["CORE_SEL"]["LSB"]
  core_dep_shift = localenv["CFG"]["CORE_DEPENDENT"]["LSB"]
  delay_comp_shift = localenv["CFG"]["IO_DELAY_COMPENSATION"]["LSB"]
  set_register(sw, addr, (cpol << cpol_shift) | (cpha << cpha_shift) | (lsbfirst << lsbfirst_shift)
                                              | (sspol << sspol_shift) | (0 << core_sel_shift)
                                              | (1 << core_dep_shift) | (io_delay_comp << delay_comp_shift))

  addr = localenv["CLKCFG"]["addr"]
  clockdiv_shift = localenv["CLKCFG"]["DIV"]["LSB"]
  set_register(sw, addr, (div << clockdiv_shift))

  addr = localenv["SPI_LEN"]["addr"]
  spilen_shift = localenv["SPI_LEN"]["VAL"]["LSB"]
  set_register(sw, addr, (txlen << spilen_shift))

  en_shift = localenv["CTRL"]["EN"]["LSB"]
  addr = localenv["CTRL"]["addr"]
  set_register_8bit(sw, addr, en << en_shift)


def configure_drive_i2c_0(sw, en=1, div=3, ssel=0):
  localenv = FPGA_Reg.registers["wfg_drive_i2c_top_0"]

  addr = localenv["CFG"]["addr"]
  devid_shift = localenv["CFG"]["DEV_ID"]["LSB"]
  set_register(sw, addr, (ssel << devid_shift))

  addr = localenv["CLKCFG"]["addr"]
  clockdiv_shift = localenv["CLKCFG"]["DIV"]["LSB"]
  set_register(sw, addr, (div << clockdiv_shift))

  en_shift = localenv["CTRL"]["EN"]["LSB"]
  addr = localenv["CTRL"]["addr"]
  set_register_8bit(sw, addr, en << en_shift)


def configure_drive_uart_0(sw, en=1, div=32, txlen=8, paritysel=0, stopsel=0, txdelay=0, shiftdir=0):
  localenv = FPGA_Reg.registers["wfg_drive_uart_top_0"]

  core_sel_shift = localenv["CFG"]["CORE_SEL"]["LSB"]
  txsize_shift = localenv["CFG"]["TXSIZE"]["LSB"]
  cdiv_shift = localenv["CFG"]["CDIV"]["LSB"]
  addr = localenv["CFG"]["addr"]
  set_register(sw, addr, (0 << core_sel_shift) | (txlen << txsize_shift) | (div << cdiv_shift))

  paritysel_shift = localenv["CFG2"]["PARITY_SEL"]["LSB"]
  stopsel_shift = localenv["CFG2"]["STOP_SEL"]["LSB"]
  txdelay_shift = localenv["CFG2"]["TX_DELAY"]["LSB"]
  shiftdir_shift = localenv["CFG2"]["SHIFT_DIR"]["LSB"]
  addr = localenv["CFG2"]["addr"]
  set_register(sw, addr, (paritysel << paritysel_shift) | (stopsel << stopsel_shift) | (txdelay << txdelay_shift) | (shiftdir << shiftdir_shift))

  en_shift = localenv["CTRL"]["EN"]["LSB"]
  addr = localenv["CTRL"]["addr"]
  set_register_8bit(sw, addr, en << en_shift)



def configure_drive_pat_0(sw, en=0xFFFF, core_sel=0, pat=0, begin=0, end=8):
  localenv = FPGA_Reg.registers["wfg_drive_pat_top_0"]

  begin_shift = localenv["CFG"]["BEGIN"]["LSB"]
  end_shift = localenv["CFG"]["END"]["LSB"]
  core_sel_shift = localenv["CFG"]["CORE_SEL"]["LSB"]
  addr = localenv["CFG"]["addr"]
  set_register(sw, addr, (begin << begin_shift) | (end << end_shift) | (0 << core_sel_shift))

  patsel_shift = localenv["PATSEL0"]["LOW"]["LSB"]
  addr = localenv["PATSEL0"]["addr"]
  set_register(sw, addr, pat[0] << patsel_shift)
  patsel_shift = localenv["PATSEL1"]["HIGH"]["LSB"]
  addr = localenv["PATSEL1"]["addr"]
  set_register(sw, addr, pat[1] << patsel_shift)

  en_shift = localenv["CTRL"]["EN"]["LSB"]
  addr = localenv["CTRL"]["addr"]
  set_register_8bit(sw, addr, en << en_shift)



def configure_pin_mux(sw, output_pin_a1=0,  pullup_pin_a1=0,  input_pin_a1=0xff,
                                                output_pin_a2=0,  pullup_pin_a2=0,  input_pin_a2=0xff,
                                                output_pin_a3=0,  pullup_pin_a3=0,  input_pin_a3=0xff,
                                                output_pin_a4=0,  pullup_pin_a4=0,  input_pin_a4=0xff,
                                                output_pin_a7=0,  pullup_pin_a7=0,  input_pin_a7=0xff,
                                                output_pin_a8=0,  pullup_pin_a8=0,  input_pin_a8=0xff,
                                                output_pin_a9=0,  pullup_pin_a9=0,  input_pin_a9=0xff,
                                                output_pin_a10=0, pullup_pin_a10=0, input_pin_a10=0xff,
                                                output_pin_b1=0,  pullup_pin_b1=0,  input_pin_b1=0xff,
                                                output_pin_b2=0,  pullup_pin_b2=0,  input_pin_b2=0xff,
                                                output_pin_b3=0,  pullup_pin_b3=0,  input_pin_b3=0xff,
                                                output_pin_b4=0,  pullup_pin_b4=0,  input_pin_b4=0xff,
                                                output_pin_b7=0,  pullup_pin_b7=0,  input_pin_b7=0xff,
                                                output_pin_b8=0,  pullup_pin_b8=0,  input_pin_b8=0xff,
                                                output_pin_b9=0,  pullup_pin_b9=0,  input_pin_b9=0xff,
                                                output_pin_b10=0, pullup_pin_b10=0, input_pin_b10=0xff

                                                ):
  localenv = FPGA_Reg.registers["wfg_pin_mux_top"]

  addr = localenv["OUTPUT_SEL_0"]["addr"]
  pingroup = 0
  if output_pin_a1 != 0:
    pingroup |= output_pin_a1 << localenv["OUTPUT_SEL_0"]["0"]["LSB"]
  if output_pin_a2 != 0:
    pingroup |= output_pin_a2 << localenv["OUTPUT_SEL_0"]["1"]["LSB"]
  if output_pin_a3 != 0:
    pingroup |= output_pin_a3 << localenv["OUTPUT_SEL_0"]["2"]["LSB"]
  if output_pin_a4 != 0:
    pingroup |= output_pin_a4 << localenv["OUTPUT_SEL_0"]["3"]["LSB"]
  if pingroup != 0:
    set_register(sw, addr, pingroup)

  addr = localenv["OUTPUT_SEL_1"]["addr"]
  pingroup = 0
  if output_pin_a7 != 0:
    pingroup |= output_pin_a7 << localenv["OUTPUT_SEL_1"]["4"]["LSB"]
  if output_pin_a8 != 0:
    pingroup |= output_pin_a8 << localenv["OUTPUT_SEL_1"]["5"]["LSB"]
  if output_pin_a9 != 0:
    pingroup |= output_pin_a9 << localenv["OUTPUT_SEL_1"]["6"]["LSB"]
  if output_pin_a10 != 0:
    pingroup |= output_pin_a10 << localenv["OUTPUT_SEL_1"]["7"]["LSB"]
  if pingroup != 0:
    set_register(sw, addr, pingroup)

  addr = localenv["OUTPUT_SEL_2"]["addr"]
  pingroup = 0
  if output_pin_b1 != 0:
    pingroup |= output_pin_b1 << localenv["OUTPUT_SEL_2"]["8"]["LSB"]
  if output_pin_b2 != 0:
    pingroup |= output_pin_b2 << localenv["OUTPUT_SEL_2"]["9"]["LSB"]
  if output_pin_b3 != 0:
    pingroup |= output_pin_b3 << localenv["OUTPUT_SEL_2"]["10"]["LSB"]
  if output_pin_b4 != 0:
    pingroup |= output_pin_b4 << localenv["OUTPUT_SEL_2"]["11"]["LSB"]
  if pingroup != 0:
    set_register(sw, addr, pingroup)

  addr = localenv["OUTPUT_SEL_3"]["addr"]
  pingroup = 0
  if output_pin_b7 != 0:
    pingroup |= output_pin_b7 << localenv["OUTPUT_SEL_3"]["12"]["LSB"]
  if output_pin_b8 != 0:
    pingroup |= output_pin_b8 << localenv["OUTPUT_SEL_3"]["13"]["LSB"]
  if output_pin_b9 != 0:
    pingroup |= output_pin_b9 << localenv["OUTPUT_SEL_3"]["14"]["LSB"]
  if output_pin_b10 != 0:
    pingroup |= output_pin_b10 << localenv["OUTPUT_SEL_3"]["15"]["LSB"]
  if pingroup != 0:
    set_register(sw, addr, pingroup)

  addr = localenv["PULLUP_SEL_0"]["addr"]
  pingroup = 0
  if pullup_pin_a1 != 0:
    pingroup |= pullup_pin_a1 << localenv["PULLUP_SEL_0"]["0"]["LSB"]
  if pullup_pin_a2 != 0:
    pingroup |= pullup_pin_a2 << localenv["PULLUP_SEL_0"]["1"]["LSB"]
  if pullup_pin_a3 != 0:
    pingroup |= pullup_pin_a3 << localenv["PULLUP_SEL_0"]["2"]["LSB"]
  if pullup_pin_a4 != 0:
    pingroup |= pullup_pin_a4 << localenv["PULLUP_SEL_0"]["3"]["LSB"]
  if pingroup != 0:
    set_register(sw, addr, pingroup)

  addr = localenv["PULLUP_SEL_1"]["addr"]
  pingroup = 0
  if pullup_pin_a7 != 0:
    pingroup |= pullup_pin_a7 << localenv["PULLUP_SEL_1"]["4"]["LSB"]
  if pullup_pin_a8 != 0:
    pingroup |= pullup_pin_a8 << localenv["PULLUP_SEL_1"]["5"]["LSB"]
  if pullup_pin_a9 != 0:
    pingroup |= pullup_pin_a9 << localenv["PULLUP_SEL_1"]["6"]["LSB"]
  if pullup_pin_a10 != 0:
    pingroup |= pullup_pin_a10 << localenv["PULLUP_SEL_1"]["7"]["LSB"]
  if pingroup != 0:
    set_register(sw, addr, pingroup)

  addr = localenv["PULLUP_SEL_2"]["addr"]
  pingroup = 0
  if pullup_pin_b1 != 0:
    pingroup |= pullup_pin_b1 << localenv["PULLUP_SEL_2"]["8"]["LSB"]
  if pullup_pin_b2 != 0:
    pingroup |= pullup_pin_b2 << localenv["PULLUP_SEL_2"]["9"]["LSB"]
  if pullup_pin_b3 != 0:
    pingroup |= pullup_pin_b3 << localenv["PULLUP_SEL_2"]["10"]["LSB"]
  if pullup_pin_b4 != 0:
    pingroup |= pullup_pin_b4 << localenv["PULLUP_SEL_2"]["11"]["LSB"]
  if pingroup != 0:
    set_register(sw, addr, pingroup)

  addr = localenv["PULLUP_SEL_3"]["addr"]
  pingroup = 0
  if pullup_pin_b7 != 0:
    pingroup |= pullup_pin_b7 << localenv["PULLUP_SEL_3"]["12"]["LSB"]
  if pullup_pin_b8 != 0:
    pingroup |= pullup_pin_b8 << localenv["PULLUP_SEL_3"]["13"]["LSB"]
  if pullup_pin_b9 != 0:
    pingroup |= pullup_pin_b9 << localenv["PULLUP_SEL_3"]["14"]["LSB"]
  if pullup_pin_b10 != 0:
    pingroup |= pullup_pin_b10 << localenv["PULLUP_SEL_3"]["15"]["LSB"]
  if pingroup != 0:
    set_register(sw, addr, pingroup)

  addr = localenv["INPUT_SEL_0"]["addr"]
  pingroup = 0
  if input_pin_a1 != 0:
    pingroup |= input_pin_a1 << localenv["INPUT_SEL_0"]["0"]["LSB"]
  if input_pin_a2 != 0:
    pingroup |= input_pin_a2 << localenv["INPUT_SEL_0"]["1"]["LSB"]
  if input_pin_a3 != 0:
    pingroup |= input_pin_a3 << localenv["INPUT_SEL_0"]["2"]["LSB"]
  if input_pin_a4 != 0:
    pingroup |= input_pin_a4 << localenv["INPUT_SEL_0"]["3"]["LSB"]
  if pingroup != 0xffffffff:
    set_register(sw, addr, pingroup)

  addr = localenv["INPUT_SEL_1"]["addr"]
  pingroup = 0
  if input_pin_a7 != 0:
    pingroup |= input_pin_a7 << localenv["INPUT_SEL_1"]["4"]["LSB"]
  if input_pin_a8 != 0:
    pingroup |= input_pin_a8 << localenv["INPUT_SEL_1"]["5"]["LSB"]
  if input_pin_a9 != 0:
    pingroup |= input_pin_a9 << localenv["INPUT_SEL_1"]["6"]["LSB"]
  if input_pin_a10 != 0:
    pingroup |= input_pin_a10 << localenv["INPUT_SEL_1"]["7"]["LSB"]
  if pingroup != 0xffffffff:
    set_register(sw, addr, pingroup)

  addr = localenv["INPUT_SEL_2"]["addr"]
  pingroup = 0
  if input_pin_b1 != 0:
    pingroup |= input_pin_b1 << localenv["INPUT_SEL_2"]["8"]["LSB"]
  if input_pin_b2 != 0:
    pingroup |= input_pin_b2 << localenv["INPUT_SEL_2"]["9"]["LSB"]
  if input_pin_b3 != 0:
    pingroup |= input_pin_b3 << localenv["INPUT_SEL_2"]["10"]["LSB"]
  if input_pin_b4 != 0:
    pingroup |= input_pin_b4 << localenv["INPUT_SEL_2"]["11"]["LSB"]
  if pingroup != 0xffffffff:
    set_register(sw, addr, pingroup)

  addr = localenv["INPUT_SEL_3"]["addr"]
  pingroup = 0
  if input_pin_b7 != 0:
    pingroup |= input_pin_b7 << localenv["INPUT_SEL_3"]["12"]["LSB"]
  if input_pin_b8 != 0:
    pingroup |= input_pin_b8 << localenv["INPUT_SEL_3"]["13"]["LSB"]
  if input_pin_b9 != 0:
    pingroup |= input_pin_b9 << localenv["INPUT_SEL_3"]["14"]["LSB"]
  if input_pin_b10 != 0:
    pingroup |= input_pin_b10 << localenv["INPUT_SEL_3"]["15"]["LSB"]
  if pingroup != 0xffffffff:
    set_register(sw, addr, pingroup)





def debug(x):
  if x != "Register, 40000, 0":
    print(x)

def readback(recId, values):
  print("readback", recId, values)

def main():

    start = time.time()
    with SmartWave().connect() as sw:
        sw.debugCallback = debug
        with sw.createI2CConfig(sda_pin_name="A3", scl_pin_name="A4") as i2c:

            # res = i2c.write(0x20, [0x55, 0xff, 0xaa])
            device_ids = i2c.scanAdresses()
            pass



    print("elapsed time: ", time.time() - start)
    print(device_ids)


if __name__ == "__main__":
    main()

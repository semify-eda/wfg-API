# Angular rate sensitivity and register config values
gyro_sense = {'125_dps': 4.37e-3,
              '250_dps': 8.75e-3,
              '500_dps': 17.5e-3,
              '1000_dps': 35.0e-3,
              '2000_dps': 70.0e-3,
              '4000_dps': 140.0e-3
              }

gyro_odr = {'pwr_down': 0b0000,
            '12.5Hz': 0b0001,
            '26Hz': 0b0010,
            '52Hz': 0b0011,
            '104Hz': 0b0100,
            '208Hz': 0b0101,
            '416Hz': 0b0110,
            '833Hz': 0b0111,
            '1667Hz': 0b1000,
            '3333Hz': 0b1001,
            '6667Hz': 0b1010
            }

gyro_fs_g = {'250_dps': 0b00,
             '500_dps': 0b01,
             '1000_dps': 0b10,
             '2000_dps': 0b11
             }

gyro_fs_125 = {'fs_g': 0b00,
               '125_dps': 0b01
               }

gyro_fs_4000 = {'fs_g': 0b00,
                '4000_dps': 0b01
                }

# Linear acceleration sensitivity and register config values
axl_sens = {'2g': 0.061e-3,
            '4g': 0.122e-3,
            '8g': 0.244e-3,
            '16g': 0.488e-3
            }

axl_odr = {'pwr_down': 0b0000,
           '12.5Hz': 0b0001,
           '26Hz': 0b0010,
           '52Hz': 0b0011,
           '104Hz': 0b0100,
           '208Hz': 0b0101,
           '416Hz': 0b0110,
           '833Hz': 0b0111,
           '1667Hz': 0b1000,
           '3333Hz': 0b1001,
           '6667Hz': 0b1010
           }

axl_fs = {'2g': 0b00,
          '16g': 0b01,
          '4g': 0b10,
          '8g': 0b11
          }

io_exp_back = [[0xef, 0xf7], [0xcf, 0xf3], [0x8f, 0xf1], [0x0f, 0xf0]]
io_exp_front = [[0xf7, 0xef], [0xf3, 0xcf], [0xf1, 0x8f], [0xf0, 0x0f]]
io_exp_right = [[0xeb, 0xff], [0xaa, 0xff], [0x82, 0xff], [0x00, 0xff]]
io_exp_left = [[0xff, 0xeb], [0xff, 0xaa], [0xff, 0x82], [0xff, 0x00]]

"""
Register settings used to configure the ASM330LHHXG1 IMU Sensor
Along with an LED toggle function, when used with the IO expander
"""

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

io_exp_front = [[0xf7, 0xff], [0xf3, 0xff], [0xf1, 0xff], [0xf0, 0xff]]
io_exp_back = [[0xef, 0xff], [0xcf, 0xff], [0x8f, 0xff], [0x0f, 0xff]]
io_exp_right = [[0xff, 0xef], [0xff, 0xcf], [0xff, 0x8f], [0xff, 0x0f]]
io_exp_left = [[0xff, 0xf7], [0xff, 0xf3], [0xff, 0xf1], [0xff, 0xf0]]


def io_led_toggle(i2c, i2c_addr, x_res, y_res):
    """
    This method uses the IO expander to control the LEDs,
    visualizing the movement of the IMU sensor based on positional values read from its registers.

    :param i2c: I2C object for SmartWave connection to the IO expander
    :param i2c_addr: Default I2C address of the IO expander
    :param x_res: Positional value from the ASM330LHHXG1 IMU Sensor
    :param y_res: Positional value from the ASM330LHHXG1 IMU Sensor
    :return: None
    """

    if (-1 < y_res < 1) and (-1 < x_res < 1):
        i2c.write(i2c_addr, [0xff, 0xff])

    # Tilting Forwards and Left
    if (-3 < y_res < -1) and (-1 < x_res < 1):
        i2c.write(i2c_addr, [io_exp_front[0][0], 0xff])
    if (-6 < y_res < -3) and (-1 < x_res < 1):
        i2c.write(i2c_addr, [io_exp_front[1][0], 0xff])
    if (-8 < y_res < -6) and (-1 < x_res < 1):
        i2c.write(i2c_addr, [io_exp_front[2][0], 0xff])
    if (y_res < -8) and (-1 < x_res < 1):
        i2c.write(i2c_addr, [io_exp_front[3][0], 0xff])

    if (-3 < y_res < -1) and (1 < x_res < 3):
        i2c.write(i2c_addr, [io_exp_front[0][0], io_exp_left[0][1]])
    if (-6 < y_res < -3) and (1 < x_res < 3):
        i2c.write(i2c_addr, [io_exp_front[1][0], io_exp_left[0][1]])
    if (-8 < y_res < -6) and (1 < x_res < 3):
        i2c.write(i2c_addr, [io_exp_front[2][0], io_exp_left[0][1]])
    if (y_res < -8) and (1 < x_res < 3):
        i2c.write(i2c_addr, [io_exp_front[3][0], io_exp_left[0][1]])

    if (-3 < y_res < -1) and (3 < x_res < 6):
        i2c.write(i2c_addr, [io_exp_front[0][0], io_exp_left[1][1]])
    if (-6 < y_res < -3) and (3 < x_res < 6):
        i2c.write(i2c_addr, [io_exp_front[1][0], io_exp_left[1][1]])
    if (-8 < y_res < -6) and (3 < x_res < 6):
        i2c.write(i2c_addr, [io_exp_front[2][0], io_exp_left[1][1]])
    if (y_res < -8) and (3 < x_res < 6):
        i2c.write(i2c_addr, [io_exp_front[3][0], io_exp_left[1][1]])

    if (-3 < y_res < -1) and (6 < x_res < 8):
        i2c.write(i2c_addr, [io_exp_front[0][0], io_exp_left[2][1]])
    if (-6 < y_res < -3) and (6 < x_res < 8):
        i2c.write(i2c_addr, [io_exp_front[1][0], io_exp_left[2][1]])
    if (-8 < y_res < -6) and (6 < x_res < 8):
        i2c.write(i2c_addr, [io_exp_front[2][0], io_exp_left[2][1]])
    if (y_res < -8) and (6 < x_res < 8):
        i2c.write(i2c_addr, [io_exp_front[3][0], io_exp_left[2][1]])

    if (-3 < y_res < -1) and (x_res >= 8):
        i2c.write(i2c_addr, [io_exp_front[0][0], io_exp_left[3][1]])
    if (-6 < y_res < -3) and (x_res > 8):
        i2c.write(i2c_addr, [io_exp_front[1][0], io_exp_left[3][1]])
    if (-8 < y_res < -6) and (x_res >= 8):
        i2c.write(i2c_addr, [io_exp_front[2][0], io_exp_left[3][1]])
    if (y_res < -8) and (x_res >= 8):
        i2c.write(i2c_addr, [io_exp_front[3][0], io_exp_left[3][1]])

    # Tilting Forwards and Right
    if (-3 < y_res < -1) and (-1 < x_res < 1):
        i2c.write(i2c_addr, [io_exp_front[0][0], 0xff])
    if (-6 < y_res < -3) and (-1 < x_res < 1):
        i2c.write(i2c_addr, [io_exp_front[1][0], 0xff])
    if (-8 < y_res < -6) and (-1 < x_res < 1):
        i2c.write(i2c_addr, [io_exp_front[2][0], 0xff])
    if (y_res < -8) and (-1 < x_res < 1):
        i2c.write(i2c_addr, [io_exp_front[3][0], 0xff])

    if (-3 < y_res < -1) and (-3 < x_res < -1):
        i2c.write(i2c_addr, [io_exp_front[0][0], io_exp_right[0][1]])
    if (-6 < y_res < -3) and (-3 < x_res < -1):
        i2c.write(i2c_addr, [io_exp_front[1][0], io_exp_right[0][1]])
    if (-8 < y_res < -6) and (-3 < x_res < -1):
        i2c.write(i2c_addr, [io_exp_front[2][0], io_exp_right[0][1]])
    if (y_res < -8) and (-3 < x_res < -1):
        i2c.write(i2c_addr, [io_exp_front[3][0], io_exp_right[0][1]])

    if (-3 < y_res < -1) and (-6 < x_res < -3):
        i2c.write(i2c_addr, [io_exp_front[0][0], io_exp_right[1][1]])
    if (-6 < y_res < -3) and (-6 < x_res < -3):
        i2c.write(i2c_addr, [io_exp_front[1][0], io_exp_right[1][1]])
    if (-8 < y_res < -6) and (-6 < x_res < -3):
        i2c.write(i2c_addr, [io_exp_front[2][0], io_exp_right[1][1]])
    if (y_res < -8) and (-6 < x_res < -3):
        i2c.write(i2c_addr, [io_exp_front[3][0], io_exp_right[1][1]])

    if (-3 < y_res < -1) and (-8 < x_res < -6):
        i2c.write(i2c_addr, [io_exp_front[0][0], io_exp_right[2][1]])
    if (-6 < y_res < -3) and (-8 < x_res < -6):
        i2c.write(i2c_addr, [io_exp_front[1][0], io_exp_right[2][1]])
    if (-8 < y_res < -6) and (-8 < x_res < -6):
        i2c.write(i2c_addr, [io_exp_front[2][0], io_exp_right[2][1]])
    if (y_res < -8) and (-8 < x_res < -6):
        i2c.write(i2c_addr, [io_exp_front[3][0], io_exp_right[2][1]])

    if (-3 < y_res < -1) and (x_res < -8):
        i2c.write(i2c_addr, [io_exp_front[0][0], io_exp_right[3][1]])
    if (-6 < y_res < -3) and (x_res < -8):
        i2c.write(i2c_addr, [io_exp_front[1][0], io_exp_right[3][1]])
    if (-8 < y_res < -6) and (x_res < -8):
        i2c.write(i2c_addr, [io_exp_front[2][0], io_exp_right[3][1]])
    if (y_res < -8) and (x_res < -8):
        i2c.write(i2c_addr, [io_exp_front[3][0], io_exp_right[3][1]])

    #########################################################################

    # Tilting Right and Forwards
    if (-3 < x_res < -1) and (-1 < y_res < 1):
        i2c.write(i2c_addr, [0xff, io_exp_right[0][1]])
    if (-6 < x_res < -3) and (-1 < y_res < 1):
        i2c.write(i2c_addr, [0xff, io_exp_right[1][1]])
    if (-8 < x_res < -6) and (-1 < y_res < 1):
        i2c.write(i2c_addr, [0xff, io_exp_right[2][1]])
    if (x_res < -8) and (-1 < y_res < 1):
        i2c.write(i2c_addr, [0xff, io_exp_right[3][1]])

    if (-3 < x_res < -1) and (-3 < y_res < -1):
        i2c.write(i2c_addr, [io_exp_front[0][0], io_exp_right[0][1]])
    if (-6 < x_res < -3) and (-3 < y_res < -1):
        i2c.write(i2c_addr, [io_exp_front[0][0], io_exp_right[1][1]])
    if (-8 < x_res < -6) and (-3 < y_res < -1):
        i2c.write(i2c_addr, [io_exp_front[0][0], io_exp_right[2][1]])
    if (x_res < -8) and (-3 < y_res < -1):
        i2c.write(i2c_addr, [io_exp_front[0][0], io_exp_right[3][1]])

    if (-3 < x_res < -1) and (-6 < y_res < -3):
        i2c.write(i2c_addr, [io_exp_front[1][0], io_exp_right[0][1]])
    if (-6 < x_res < -3) and (-6 < y_res < -3):
        i2c.write(i2c_addr, [io_exp_front[1][0], io_exp_right[1][1]])
    if (-8 < x_res < -6) and (-6 < y_res < -3):
        i2c.write(i2c_addr, [io_exp_front[1][0], io_exp_right[2][1]])
    if (x_res < -8) and (-6 < y_res < -3):
        i2c.write(i2c_addr, [io_exp_front[1][0], io_exp_right[3][1]])

    if (-3 < x_res < -1) and (-8 < y_res < -6):
        i2c.write(i2c_addr, [io_exp_front[2][0], io_exp_right[0][1]])
    if (-6 < x_res < -3) and (-8 < y_res < -6):
        i2c.write(i2c_addr, [io_exp_front[2][0], io_exp_right[1][1]])
    if (-8 < x_res < -6) and (-8 < y_res < -6):
        i2c.write(i2c_addr, [io_exp_front[2][0], io_exp_right[2][1]])
    if (x_res < -8) and (-8 < y_res < -6):
        i2c.write(i2c_addr, [io_exp_front[2][0], io_exp_right[3][1]])

    if (-3 < x_res < -1) and (y_res < -8):
        i2c.write(i2c_addr, [io_exp_front[3][0], io_exp_right[0][1]])
    if (-6 < x_res < -3) and (y_res < -8):
        i2c.write(i2c_addr, [io_exp_front[3][0], io_exp_right[1][1]])
    if (-7 < x_res < -6) and (y_res < -8):
        i2c.write(i2c_addr, [io_exp_front[3][0], io_exp_right[2][1]])
    if (x_res < -8) and (y_res < -8):
        i2c.write(i2c_addr, [io_exp_front[3][0], io_exp_right[3][1]])

    # Tilting Left and Forwards
    if (1 < x_res < 3) and (-1 < y_res < 1):
        i2c.write(i2c_addr, [0xff, io_exp_left[0][1]])
    if (3 < x_res < 6) and (-1 < y_res < 1):
        i2c.write(i2c_addr, [0xff, io_exp_left[1][1]])
    if (6 < x_res < 8) and (-1 < y_res < 1):
        i2c.write(i2c_addr, [0xff, io_exp_left[2][1]])
    if (x_res >= 8) and (-1 < y_res < 1):
        i2c.write(i2c_addr, [0xff, io_exp_left[3][1]])

    if (1 < x_res < 3) and (-3 < y_res < -1):
        i2c.write(i2c_addr, [io_exp_front[0][0], io_exp_left[0][1]])
    if (3 < x_res < 6) and (-3 < y_res < -1):
        i2c.write(i2c_addr, [io_exp_front[0][0], io_exp_left[1][1]])
    if (6 < x_res < 8) and (-3 < y_res < -1):
        i2c.write(i2c_addr, [io_exp_front[0][0], io_exp_left[2][1]])
    if (x_res >= 8) and (-3 < y_res < -1):
        i2c.write(i2c_addr, [io_exp_front[0][0], io_exp_left[3][1]])

    if (1 < x_res < 3) and (-6 < y_res < -3):
        i2c.write(i2c_addr, [io_exp_front[1][0], io_exp_left[0][1]])
    if (3 < x_res < 6) and (-6 < y_res < -3):
        i2c.write(i2c_addr, [io_exp_front[1][0], io_exp_left[1][1]])
    if (6 < x_res < 8) and (-6 < y_res < -3):
        i2c.write(i2c_addr, [io_exp_front[1][0], io_exp_left[2][1]])
    if (x_res >= 8) and (-6 < y_res < -3):
        i2c.write(i2c_addr, [io_exp_front[1][0], io_exp_left[3][1]])

    if (1 < x_res < 3) and (-8 < y_res < -6):
        i2c.write(i2c_addr, [io_exp_front[2][0], io_exp_left[0][1]])
    if (3 < x_res < 6) and (-8 < y_res < -6):
        i2c.write(i2c_addr, [io_exp_front[2][0], io_exp_left[1][1]])
    if (6 < x_res < 8) and (-8 < y_res < -6):
        i2c.write(i2c_addr, [io_exp_front[2][0], io_exp_left[2][1]])
    if (x_res >= 8) and (-8 < y_res < -6):
        i2c.write(i2c_addr, [io_exp_front[2][0], io_exp_left[3][1]])

    if (1 < x_res < 3) and (y_res < - 8):
        i2c.write(i2c_addr, [io_exp_front[3][0], io_exp_left[0][1]])
    if (3 < x_res < 6) and (y_res < - 8):
        i2c.write(i2c_addr, [io_exp_front[3][0], io_exp_left[1][1]])
    if (6 < x_res < 8) and (y_res < - 8):
        i2c.write(i2c_addr, [io_exp_front[3][0], io_exp_left[2][1]])
    if (x_res >= 8) and (y_res < - 8):
        i2c.write(i2c_addr, [io_exp_front[3][0], io_exp_left[3][1]])

    #########################################################################

    # Tilting Backwards and Left
    if (1 < y_res < 3) and (-1 < x_res < 1):
        i2c.write(i2c_addr, [io_exp_back[0][0], 0xff])
    if (3 < y_res < 6) and (-1 < x_res < 1):
        i2c.write(i2c_addr, [io_exp_back[1][0], 0xff])
    if (6 < y_res < 8) and (-1 < x_res < 1):
        i2c.write(i2c_addr, [io_exp_back[2][0], 0xff])
    if (y_res >= 8) and (-1 < x_res < 1):
        i2c.write(i2c_addr, [io_exp_back[3][0], 0xff])

    if (1 < y_res < 3) and (1 < x_res < 3):
        i2c.write(i2c_addr, [io_exp_back[0][0], io_exp_left[0][1]])
    if (3 < y_res < 6) and (1 < x_res < 3):
        i2c.write(i2c_addr, [io_exp_back[1][0], io_exp_left[0][1]])
    if (6 < y_res < 8) and (1 < x_res < 3):
        i2c.write(i2c_addr, [io_exp_back[2][0], io_exp_left[0][1]])
    if (y_res >= 8) and (1 < x_res < 3):
        i2c.write(i2c_addr, [io_exp_back[3][0], io_exp_left[0][1]])

    if (1 < y_res < 3) and (3 < x_res < 6):
        i2c.write(i2c_addr, [io_exp_back[0][0], io_exp_left[1][1]])
    if (3 < y_res < 6) and (3 < x_res < 6):
        i2c.write(i2c_addr, [io_exp_back[1][0], io_exp_left[1][1]])
    if (6 < y_res < 8) and (3 < x_res < 6):
        i2c.write(i2c_addr, [io_exp_back[2][0], io_exp_left[1][1]])
    if (y_res >= 8) and (3 < x_res < 6):
        i2c.write(i2c_addr, [io_exp_back[3][0], io_exp_left[1][1]])

    if (1 < y_res < 3) and (6 < x_res < 8):
        i2c.write(i2c_addr, [io_exp_back[0][0], io_exp_left[2][1]])
    if (3 < y_res < 6) and (6 < x_res < 8):
        i2c.write(i2c_addr, [io_exp_back[1][0], io_exp_left[2][1]])
    if (6 < y_res < 8) and (6 < x_res < 8):
        i2c.write(i2c_addr, [io_exp_back[2][0], io_exp_left[2][1]])
    if (y_res >= 8) and (6 < x_res < 8):
        i2c.write(i2c_addr, [io_exp_back[3][0], io_exp_left[2][1]])

    if (1 < y_res < 3) and (x_res >= 8):
        i2c.write(i2c_addr, [io_exp_back[0][0], io_exp_left[3][1]])
    if (3 < y_res < 6) and (x_res >= 8):
        i2c.write(i2c_addr, [io_exp_back[1][0], io_exp_left[3][1]])
    if (6 < y_res < 8) and (x_res >= 8):
        i2c.write(i2c_addr, [io_exp_back[2][0], io_exp_left[3][1]])
    if (y_res >= 8) and (x_res >= 8):
        i2c.write(i2c_addr, [io_exp_back[3][0], io_exp_left[3][1]])

    # Tilting Backwards and Right
    if (1 < y_res < 3) and (-1 < x_res < 1):
        i2c.write(i2c_addr, [io_exp_back[0][0], 0xff])
    if (3 < y_res < 6) and (-1 < x_res < 1):
        i2c.write(i2c_addr, [io_exp_back[1][0], 0xff])
    if (6 < y_res < 8) and (-1 < x_res < 1):
        i2c.write(i2c_addr, [io_exp_back[2][0], 0xff])
    if (y_res >= 8) and (-1 < x_res < 1):
        i2c.write(i2c_addr, [io_exp_back[3][0], 0xff])

    if (1 < y_res < 3) and (-3 < x_res < -1):
        i2c.write(i2c_addr, [io_exp_back[0][0], io_exp_right[0][1]])
    if (3 < y_res < 6) and (-3 < x_res < -1):
        i2c.write(i2c_addr, [io_exp_back[1][0], io_exp_right[0][1]])
    if (6 < y_res < 8) and (-3 < x_res < -1):
        i2c.write(i2c_addr, [io_exp_back[2][0], io_exp_right[0][1]])
    if (y_res >= 8) and (-3 < x_res < -1):
        i2c.write(i2c_addr, [io_exp_back[3][0], io_exp_right[0][1]])

    if (1 < y_res < 3) and (-6 < x_res < -3):
        i2c.write(i2c_addr, [io_exp_back[0][0], io_exp_right[1][1]])
    if (3 < y_res < 6) and (-6 < x_res < -3):
        i2c.write(i2c_addr, [io_exp_back[1][0], io_exp_right[1][1]])
    if (6 < y_res < 8) and (-6 < x_res < -3):
        i2c.write(i2c_addr, [io_exp_back[2][0], io_exp_right[1][1]])
    if (y_res >= 8) and (-6 < x_res < -3):
        i2c.write(i2c_addr, [io_exp_back[3][0], io_exp_right[1][1]])

    if (1 < y_res < 3) and (-7 < x_res < -6):
        i2c.write(i2c_addr, [io_exp_back[0][0], io_exp_right[2][1]])
    if (3 < y_res < 6) and (-7 < x_res < -6):
        i2c.write(i2c_addr, [io_exp_back[1][0], io_exp_right[2][1]])
    if (6 < y_res < 8) and (-7 < x_res < -6):
        i2c.write(i2c_addr, [io_exp_back[2][0], io_exp_right[2][1]])
    if (y_res >= 8) and (-7 < x_res < -6):
        i2c.write(i2c_addr, [io_exp_back[3][0], io_exp_right[2][1]])

    if (1 < y_res < 3) and (x_res < -8):
        i2c.write(i2c_addr, [io_exp_back[0][0], io_exp_right[3][1]])
    if (3 < y_res < 6) and (x_res < -8):
        i2c.write(i2c_addr, [io_exp_back[1][0], io_exp_right[3][1]])
    if (6 < y_res < 8) and (x_res < -8):
        i2c.write(i2c_addr, [io_exp_back[2][0], io_exp_right[3][1]])
    if (y_res >= 8) and (x_res < -8):
        i2c.write(i2c_addr, [io_exp_back[3][0], io_exp_right[3][1]])

    #########################################################################

    # Tilting Right and Backwards
    if (-3 < x_res < -1) and (-1 < y_res < 1):
        i2c.write(i2c_addr, [0xff, io_exp_right[0][1]])
    if (-6 < x_res < -3) and (-1 < y_res < 1):
        i2c.write(i2c_addr, [0xff, io_exp_right[1][1]])
    if (-7 < x_res < -6) and (-1 < y_res < 1):
        i2c.write(i2c_addr, [0xff, io_exp_right[2][1]])
    if (x_res < -8) and (-1 < y_res < 1):
        i2c.write(i2c_addr, [0xff, io_exp_right[3][1]])

    if (-3 < x_res < -1) and (1 < y_res < 3):
        i2c.write(i2c_addr, [io_exp_back[0][0], io_exp_right[0][1]])
    if (-6 < x_res < -3) and (1 < y_res < 3):
        i2c.write(i2c_addr, [io_exp_back[0][0], io_exp_right[1][1]])
    if (-7 < x_res < -6) and (1 < y_res < 3):
        i2c.write(i2c_addr, [io_exp_back[0][0], io_exp_right[2][1]])
    if (x_res < -8) and (1 < y_res < 3):
        i2c.write(i2c_addr, [io_exp_back[0][0], io_exp_right[3][1]])

    if (-3 < x_res < -1) and (3 < y_res < 6):
        i2c.write(i2c_addr, [io_exp_back[1][0], io_exp_right[0][1]])
    if (-6 < x_res < -3) and (3 < y_res < 6):
        i2c.write(i2c_addr, [io_exp_back[1][0], io_exp_right[1][1]])
    if (-7 < x_res < -6) and (3 < y_res < 6):
        i2c.write(i2c_addr, [io_exp_back[1][0], io_exp_right[2][1]])
    if (x_res < -8) and (3 < y_res < 6):
        i2c.write(i2c_addr, [io_exp_back[1][0], io_exp_right[3][1]])

    if (-3 < x_res < -1) and (6 < y_res < 7):
        i2c.write(i2c_addr, [io_exp_back[2][0], io_exp_right[0][1]])
    if (-6 < x_res < -3) and (6 < y_res < 7):
        i2c.write(i2c_addr, [io_exp_back[2][0], io_exp_right[1][1]])
    if (-7 < x_res < -6) and (6 < y_res < 7):
        i2c.write(i2c_addr, [io_exp_back[2][0], io_exp_right[2][1]])
    if (x_res < -8) and (6 < y_res < 7):
        i2c.write(i2c_addr, [io_exp_back[2][0], io_exp_right[3][1]])

    if (-3 < x_res < -1) and (y_res > 8):
        i2c.write(i2c_addr, [io_exp_back[3][0], io_exp_right[0][1]])
    if (-6 < x_res < -3) and (y_res > 8):
        i2c.write(i2c_addr, [io_exp_back[3][0], io_exp_right[1][1]])
    if (-7 < x_res < -6) and (y_res > 8):
        i2c.write(i2c_addr, [io_exp_back[3][0], io_exp_right[2][1]])
    if (x_res < -8) and (y_res >= 8):
        i2c.write(i2c_addr, [io_exp_back[3][0], io_exp_right[3][1]])

    # Tilting Left and Backwards
    if (1 < x_res < 3) and (-1 < y_res < 1):
        i2c.write(i2c_addr, [0xff, io_exp_left[0][1]])
    if (3 < x_res < 6) and (-1 < y_res < 1):
        i2c.write(i2c_addr, [0xff, io_exp_left[1][1]])
    if (6 < x_res < 8) and (-1 < y_res < 1):
        i2c.write(i2c_addr, [0xff, io_exp_left[2][1]])
    if (x_res >= 8) and (-1 < y_res < 1):
        i2c.write(i2c_addr, [0xff, io_exp_left[3][1]])

    if (1 < x_res < 3) and (1 < y_res < 3):
        i2c.write(i2c_addr, [io_exp_back[0][0], io_exp_left[0][1]])
    if (3 < x_res < 6) and (1 < y_res < 3):
        i2c.write(i2c_addr, [io_exp_back[0][0], io_exp_left[1][1]])
    if (6 < x_res < 8) and (1 < y_res < 3):
        i2c.write(i2c_addr, [io_exp_back[0][0], io_exp_left[2][1]])
    if (x_res >= 8) and (1 < y_res < 3):
        i2c.write(i2c_addr, [io_exp_back[0][0], io_exp_left[3][1]])

    if (1 < x_res < 3) and (3 < y_res < 6):
        i2c.write(i2c_addr, [io_exp_back[1][0], io_exp_left[0][1]])
    if (3 < x_res < 6) and (3 < y_res < 6):
        i2c.write(i2c_addr, [io_exp_back[1][0], io_exp_left[1][1]])
    if (6 < x_res < 8) and (3 < y_res < 6):
        i2c.write(i2c_addr, [io_exp_back[1][0], io_exp_left[2][1]])
    if (x_res >= 8) and (3 < y_res < 6):
        i2c.write(i2c_addr, [io_exp_back[1][0], io_exp_left[3][1]])

    if (1 < x_res < 3) and (6 < y_res < 7):
        i2c.write(i2c_addr, [io_exp_back[2][0], io_exp_left[0][1]])
    if (3 < x_res < 6) and (6 < y_res < 7):
        i2c.write(i2c_addr, [io_exp_back[2][0], io_exp_left[1][1]])
    if (6 < x_res < 8) and (6 < y_res < 7):
        i2c.write(i2c_addr, [io_exp_back[2][0], io_exp_left[2][1]])
    if (x_res >= 8) and (6 < y_res < 7):
        i2c.write(i2c_addr, [io_exp_back[2][0], io_exp_left[3][1]])

    if (1 < x_res < 3) and (y_res >= 8):
        i2c.write(i2c_addr, [io_exp_back[3][0], io_exp_left[0][1]])
    if (3 < x_res < 6) and (y_res >= 8):
        i2c.write(i2c_addr, [io_exp_back[3][0], io_exp_left[1][1]])
    if (6 < x_res < 8) and (y_res >= 8):
        i2c.write(i2c_addr, [io_exp_back[3][0], io_exp_left[2][1]])
    if (x_res >= 8) and (y_res >= 8):
        i2c.write(i2c_addr, [io_exp_back[3][0], io_exp_left[3][1]])


"""
Demo script for the ASM330LHHXG1 IMU Sensor
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

from SmartWaveAPI import SmartWave
from imu_conf_lib import gyro_sense, gyro_odr, gyro_fs_g, gyro_fs_125, gyro_fs_4000, axl_sens, axl_odr, axl_fs
import time


def axl_conf(i2c, i2c_addr, odr='208Hz', fs='2g'):
    axl_reg = ((axl_odr[odr] << 4) + (axl_fs[fs] << 2))
    i2c.writeRegister(i2c_addr, 0x10.to_bytes(1, 'big'), axl_reg.to_bytes(1, 'big'))
    ctrl1_xl = i2c.readRegister(i2c_addr, 0x10.to_bytes(1, 'big'), 1)
    print(f"Accelerometer control register value: {bin(int.from_bytes(ctrl1_xl, 'big', signed=False))[2:].zfill(8)}")


def gyro_conf(i2c, i2c_addr, odr='208Hz', fs_g='500_dps', fs_125='fs_g', fs_4000='fs_g'):
    gyro_reg = ((gyro_odr[odr] << 4) + (gyro_fs_g[fs_g] << 2) +
                (gyro_fs_125[fs_125] << 1) + gyro_fs_4000[fs_4000])
    i2c.writeRegister(i2c_addr, 0x11.to_bytes(1, 'big'), gyro_reg.to_bytes(1, 'big'))
    ctrl2_g = i2c.readRegister(i2c_addr, 0x11.to_bytes(1, 'big'), 1)
    print(f"Gyroscope control register value: {bin(int.from_bytes(ctrl2_g, 'big', signed=False))[2:].zfill(8)}")


def twos_comp(val, bits=16):
    """Compute the two's complement of register value"""
    if(val & (1 << (bits - 1))) != 0:
        val = val - (1 << bits)
    return val


def main():
    sw = SmartWave()
    sw.connect()

    i2c_addr = 0b1101010  # Default I2C address
    i2c = sw.createI2CConfig("A1", "A2", int(200e3))

    i2c.writeRegister(
        i2c_addr,
        0x10.to_bytes(1, 'big'),
        0b00010000.to_bytes(1, 'big')
    )
    device_id = i2c.readRegister(0b1101010, 0x0f.to_bytes(1, 'big'), 1)

    if device_id[0] == 0xff:
        raise ValueError("Couldn't reach device. Terminating code.")
    else:
        print(f"Connection was successful. Device ID: {device_id[0]:#0x}")

    # Configure the ASM330LHHXG1 IMU
    axl_conf(i2c, i2c_addr)
    gyro_conf(i2c, i2c_addr)

    # Default settings for plotting
    plt.rcParams["figure.figsize"] = [7.50, 5.50]
    plt.rcParams["figure.autolayout"] = True
    x_len = 200
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1)
    xs = list(range(0, 200))

    for ax in [ax1, ax2, ax3]:
        ax.set_ylim(-20, 20)
        ax.grid()

    y1data = [0] * x_len
    y2data = [0] * x_len
    y3data = [0] * x_len
    line1, = ax1.plot(xs, y1data, lw=3)
    line2, = ax2.plot(xs, y2data, lw=3, color='r')
    line3, = ax3.plot(xs, y3data, lw=3, color='g')
    line = [line1, line2, line3]

    ys = [y1data, y2data, y3data]

    def animate(i, ys):
        # Angular rate sensor
        pitch_lsb = i2c.readRegister(i2c_addr, 0x22.to_bytes(1, 'big'), 1)
        pitch_msb = i2c.readRegister(i2c_addr, 0x23.to_bytes(1, 'big'), 1)
        pitch = (pitch_msb[0] << 8) + pitch_lsb[0]
        tc_pitch = twos_comp(pitch)

        roll_lsb = i2c.readRegister(i2c_addr, 0x24.to_bytes(1, 'big'), 1)
        roll_msb = i2c.readRegister(i2c_addr, 0x25.to_bytes(1, 'big'), 1)
        roll = (roll_msb[0] << 8) + roll_lsb[0]
        tc_roll = twos_comp(roll)

        yaw_lsb = i2c.readRegister(i2c_addr, 0x26.to_bytes(1, 'big'), 1)
        yaw_msb = i2c.readRegister(i2c_addr, 0x27.to_bytes(1, 'big'), 1)
        yaw = (yaw_msb[0] << 8) + yaw_lsb[0]
        tc_yaw = twos_comp(yaw)

        # Angular rate conversion
        pitch_res = tc_pitch * gyro_sense['500_dps']
        roll_res = tc_roll * gyro_sense['500_dps']
        yaw_res = tc_yaw * gyro_sense['500_dps']
        print(f"Pitch: {tc_pitch:.3f}     Roll: {tc_roll:.3f}    Yaw: {tc_yaw:.3f}")
        print(f"Pitch: {pitch_res:.3f}°    Roll: {roll_res:.3f}°   Yaw: {yaw_res:.3f}°\n")

        # Linear acceleration sensor
        x_axis_lsb = i2c.readRegister(i2c_addr, 0x28.to_bytes(1, 'big'), 1)
        x_axis_msb = i2c.readRegister(i2c_addr, 0x29.to_bytes(1, 'big'), 1)
        x_axis = (x_axis_msb[0] << 8) + x_axis_lsb[0]
        tc_x_axis = twos_comp(x_axis, 16)

        y_axis_lsb = i2c.readRegister(i2c_addr, 0x2A.to_bytes(1, 'big'), 1)
        y_axis_msb = i2c.readRegister(i2c_addr, 0x2B.to_bytes(1, 'big'), 1)
        y_axis = (y_axis_msb[0] << 8) + y_axis_lsb[0]
        tc_y_axis = twos_comp(y_axis, 16)

        z_axis_lsb = i2c.readRegister(i2c_addr, 0x2C.to_bytes(1, 'big'), 1)
        z_axis_msb = i2c.readRegister(i2c_addr, 0x2D.to_bytes(1, 'big'), 1)
        z_axis = (z_axis_msb[0] << 8) + z_axis_lsb[0]
        tc_z_axis = twos_comp(z_axis, 16)

        # Linear acceleration conversion # TODO: create separate function for conversion
        # convert from g to m/s^2 1 g-unit = 9.80665
        x_res = tc_x_axis * axl_sens['2g'] * 9.80665
        y_res = tc_y_axis * axl_sens['2g'] * 9.80665
        z_res = tc_z_axis * axl_sens['2g'] * 9.80665
        print(f"X_adc: {pitch:.3f}     Y_adc: {roll:.3f}    Z_adc:: {yaw:.3f}")
        print(f"X_a: {x_res:.3f} m/s^2    Y_a: {y_res:.3f} m/s^2   Z_a: {z_res:.3f} m/s^2\n")

        ys[0].append(x_res)
        ys[0] = ys[0][-x_len:]
        line[0].set_ydata(ys[0])

        ys[1].append(y_res)
        ys[1] = ys[1][-x_len:]
        line[1].set_ydata(ys[1])

        ys[2].append(z_res)
        ys[2] = ys[2][-x_len:]
        line[2].set_ydata(ys[2])

        return line

    ani = animation.FuncAnimation(fig, animate, fargs=(ys, ), interval=50, blit=True, cache_frame_data=False)
    plt.show()

    sw.disconnect()


if __name__ == "__main__":
    main()

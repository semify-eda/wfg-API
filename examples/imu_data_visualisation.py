"""
Demo script for the ASM330LHHXG1 IMU Sensor
"""

import numpy as np
from PIL import Image
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.image as image
import keyboard

from multiprocessing import Process

from SmartWaveAPI import SmartWave
from imu_conf_lib import *

matplotlib.use('TkAgg')
# This only required if the ffmpeg is not part of the system PATH - note that the file location might be different for other users
matplotlib.rcParams['animation.ffmpeg_path'] = r"C:\resources\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe"

# If True, a video is captured of the plotting
# If False, the data is visualized in real-time
SAVE_VIDEO = False

# Color scheme for plotting
sem_grey = '#323c40'
sem_white = '#f2f2f2'
sem_blue = '#43788c'
sem_dark_blue = '#2b4c59'
sem_light_grey = '#6d848c'


def axl_conf(i2c, i2c_addr, odr='208Hz', fs='2g'):
    """
    Method used to configure the accelerometer control register
    :param i2c: i2c object for SmartWave connection
    :param i2c_addr: default I2C address of the ASM330LHHXG1 IMU Sensor
    :param odr: Accelerometer output data rate selection (in Hz)
    :param fs: Accelerometer full-scale selection.
    :return: None
    """
    axl_reg = ((axl_odr[odr] << 4) + (axl_fs[fs] << 2))
    i2c.writeRegister(i2c_addr, 0x10.to_bytes(1, 'big'), axl_reg.to_bytes(1, 'big'))
    ctrl1_xl = i2c.readRegister(i2c_addr, 0x10.to_bytes(1, 'big'), 1)
    print(f"Accelerometer control register value: {ctrl1_xl[0]:08b}")


def gyro_conf(i2c, i2c_addr, odr='12.5Hz', fs_g='250_dps', fs_125='fs_g', fs_4000='4000_dps'):
    """
    Method used to configure the gyroscope control register
    :param i2c: i2c object for SmartWave connection
    :param i2c_addr: default I2C address of the ASM330LHHXG1 IMU Sensor
    :param odr: Gyroscope output data rate selection (in Hz)
    :param fs_g: Gyroscope chain full-scale selection
    :param fs_125: Selects gyroscope chain full-scale ±125 dps
    :param fs_4000: Selects gyroscope chain full-scale ±4000 dps
    :return: None
    """
    gyro_reg = ((gyro_odr[odr] << 4) + (gyro_fs_g[fs_g] << 2) +
                (gyro_fs_125[fs_125] << 1) + gyro_fs_4000[fs_4000])
    i2c.writeRegister(i2c_addr, 0x11.to_bytes(1, 'big'), gyro_reg.to_bytes(1, 'big'))
    ctrl2_g = i2c.readRegister(i2c_addr, 0x11.to_bytes(1, 'big'), 1)
    print(f"Gyroscope control register value: {ctrl2_g[0]:08b}")


def twos_comp(val, bits=16):
    """
    Compute the two's complement of register value
    :param val: Input data
    :param bits: Bit length
    :return: Two's complement of the input data
    """
    if (val & (1 << (bits - 1))) != 0:
        val = val - (1 << bits)
    return val


def main():
    """
    The main function handles the connection to SmartWave and the ASM330LHHXG1 IMU Sensor. It configures the
    accelerometer and gyroscope, sets default plotting parameters, and reads the angular and linear rate registers
    for data visualization.
    :return: None
    """
    sw = SmartWave()
    sw.connect()

    i2c_addr = 0b1101010  # Default I2C address
    i2c = sw.createI2CConfig("A1", "A2", int(200e3))

    i2c.writeRegister(i2c_addr, 0x10.to_bytes(1, 'big'), 0b00010000.to_bytes(1, 'big'))
    device_id = i2c.readRegister(i2c_addr, 0x0f.to_bytes(1, 'big'), 1)

    # Check if connection to the target device was successful
    if device_id[0] == 0xff:
        raise ValueError("Couldn't reach device. Terminating code.")
    else:
        print(f"Connection was successful. Device ID: {device_id[0]:#0x}")

    # Configure the ASM330LHHXG1 IMU
    axl_conf(i2c, i2c_addr)
    gyro_conf(i2c, i2c_addr)

    # Import semify logo for plotting
    file = "semify_logo.png"
    logo = image.imread(file)
    img = Image.open(file)
    resize = img.resize((np.array(img.size) / 17).astype(int))

    # Default settings for plotting
    plt.rcParams["figure.facecolor"] = sem_grey
    plt.rcParams["figure.figsize"] = [9.50, 7.50]
    plt.rcParams["figure.autolayout"] = True
    x_len = 200

    fig = plt.figure()
    gs = fig.add_gridspec(3, 2)
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[1, 0])
    ax3 = fig.add_subplot(gs[2, 0])
    ax4 = fig.add_subplot(gs[0, 1])
    ax5 = fig.add_subplot(gs[1, 1])
    ax6 = fig.add_subplot(gs[2, 1])

    fig.suptitle("IMU - Data Visualization", color=sem_white)
    ax1.set_title("X - axis", color=sem_white)
    ax2.set_title("Y - axis", color=sem_white)
    ax3.set_title("Z - axis", color=sem_white)

    ax4.set_title("Pitch", color=sem_white)
    ax5.set_title("Roll", color=sem_white)
    ax6.set_title("Yaw", color=sem_white)

    for ax in [ax1, ax2, ax3]:
        ax.set_ylim(-20, 20)
        ax.set_ylabel("Force (m/s^2)", color=sem_white)
        ax.set_xlabel("Samples", color=sem_white)
        ax.tick_params(labelcolor=sem_white)
        ax.grid()

    for ax in [ax4, ax5, ax6]:
        ax.set_ylim(-300, 300)
        ax.set_ylabel("Rate of Change", color=sem_white)
        ax.yaxis.set_label_position('right')
        ax.yaxis.tick_right()
        ax.set_xlabel("Samples", color=sem_white)
        ax.tick_params(labelcolor=sem_white)
        ax.grid()

    xs = list(range(0, 200))

    axl_x = [0] * x_len
    axl_y = [0] * x_len
    axl_z = [0] * x_len
    line1, = ax1.plot(xs, axl_x, lw=2, color=sem_dark_blue)
    line2, = ax2.plot(xs, axl_y, lw=2, color=sem_blue)
    line3, = ax3.plot(xs, axl_z, lw=2, color=sem_light_grey)

    gyro_x = [0] * x_len
    gyro_y = [0] * x_len
    gyro_z = [0] * x_len
    line4, = ax4.plot(xs, gyro_x, lw=2, color=sem_dark_blue)
    line5, = ax5.plot(xs, gyro_y, lw=2, color=sem_blue)
    line6, = ax6.plot(xs, gyro_z, lw=2, color=sem_light_grey)

    line = [line1, line2, line3, line4, line5, line6]
    ys = [axl_x, axl_y, axl_z, gyro_x, gyro_y, gyro_z]

    def animate(i, ys):
        """
        This function is used to animate the plotting, which enables displaying real-time data.
        :param i: Placeholder
        :param ys: List that contains data for plotting the linear rate of change
        :return: Data for plotting
        """
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

        # Angular rate conversion - returns the rate of change
        pitch_res = np.round((tc_pitch * gyro_sense['4000_dps']), 3)  # * (np.pi / 180)), 3)
        roll_res = np.round((tc_roll * gyro_sense['4000_dps']), 3)  # * (np.pi / 180)), 3)
        yaw_res = np.round((tc_yaw * gyro_sense['4000_dps']), 3)  # * (np.pi / 180)), 3)
        # print(f"Pitch: {tc_pitch:.3f}     Roll: {tc_roll:.3f}    Yaw: {tc_yaw:.3f}")
        # print(f"Pitch: {pitch_res:.3f} degrees    Roll: {roll_res:.3f} degrees   Yaw: {yaw_res:.3f} degrees\n")

        ys[3].append(pitch_res)
        ys[3] = ys[3][-x_len:]
        line[3].set_ydata(ys[3])

        ys[4].append(roll_res)
        ys[4] = ys[4][-x_len:]
        line[4].set_ydata(ys[4])

        ys[5].append(yaw_res)
        ys[5] = ys[5][-x_len:]
        line[5].set_ydata(ys[5])

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

        # Linear acceleration conversion
        # convert from g to m/s^2 1 g-unit = 9.80665
        x_res = tc_x_axis * axl_sens['2g'] * 9.80665
        y_res = tc_y_axis * axl_sens['2g'] * 9.80665
        z_res = tc_z_axis * axl_sens['2g'] * 9.80665
        # print(f"X_adc: {pitch:.3f}     Y_adc: {roll:.3f}    Z_adc:: {yaw:.3f}")
        # print(f"X_a: {x_res:.3f} m/s^2    Y_a: {y_res:.3f} m/s^2   Z_a: {z_res:.3f} m/s^2\n")

        ys[0].append(y_res)
        ys[0] = ys[0][-x_len:]
        line[0].set_ydata(ys[0])

        ys[1].append(x_res)
        ys[1] = ys[1][-x_len:]
        line[1].set_ydata(ys[1])

        ys[2].append(z_res)
        ys[2] = ys[2][-x_len:]
        line[2].set_ydata(ys[2])

        return line

    if SAVE_VIDEO:
        anim = animation.FuncAnimation(fig, animate,
                                       fargs=(ys,),
                                       interval=1,
                                       repeat=True,
                                       save_count=5000
                                       )

        file_loc = "imu.mp4"    # Saves mp4 in current working directory, update if needed
        write_vid = animation.FFMpegWriter(fps=10, extra_args=['-vcodec', 'libx264'])
        anim.save(file_loc, writer=write_vid)

    else:
        # If blit set to False, the cube gets updated real-time, but the animation becomes very slow
        # If blit is set to True, the cube won't be plotted along with the accelerometer data.
        # This requires the animate function to be modified to only return line
        anim = animation.FuncAnimation(fig, animate,
                                       fargs=(ys,),
                                       interval=10,
                                       blit=True,
                                       cache_frame_data=False)

        plt.figimage(resize, xo=1100, yo=880, origin='upper')  # TODO: dynamic positioning of image
        plt.show()
    sw.disconnect()


if __name__ == "__main__":
    process = Process(target=main)
    process.start()
    while process.is_alive():
        if keyboard.is_pressed('q'):
            process.terminate()
            break

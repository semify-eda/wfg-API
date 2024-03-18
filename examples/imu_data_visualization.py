"""
Demo script for the ASM330LHHXG1 IMU Sensor
"""
import numpy as np
import scipy.signal as signal
from PIL import Image
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation

import keyboard
import pyaudio
from multiprocessing import Process

from SmartWaveAPI import SmartWave
from imu_conf_lib import *

matplotlib.use('TkAgg')

# If set to true, include the io-expander for visualization
IO_EXPANDER = True

# If set to true, the script generates and plays a sine wave according to the IMU sensor data
PLAY_SOUND = True

# Color scheme for plotting
sem_grey = '#323c40'
sem_white = '#f2f2f2'
sem_blue = '#43788c'
sem_dark_blue = '#2b4c59'
sem_light_grey = '#6d848c'


def axl_conf(i2c, i2c_addr, odr: str = '12.5Hz', fs: str = '2g') -> None:
    """
    Method used to configure the accelerometer control register

    :param i2c: I2C object for SmartWave connection to the IMU sensor
    :param i2c_addr: Default I2C address of the ASM330LHHXG1 IMU Sensor
    :param odr: Accelerometer output data rate selection (in Hz)
    :param fs: Accelerometer full-scale selection.
    :return: None
    """
    axl_reg = ((axl_odr[odr] << 4) + (axl_fs[fs] << 2))
    i2c.writeRegister(i2c_addr, 0x10.to_bytes(1, 'big'), axl_reg.to_bytes(1, 'big'))
    ctrl1_xl = i2c.readRegister(i2c_addr, 0x10.to_bytes(1, 'big'), 1)
    print(f"Accelerometer control register value: {ctrl1_xl[0]:08b}")


def gyro_conf(i2c, i2c_addr, odr: str = '12.5Hz', fs_g: str = '250_dps',
              fs_125: str = 'fs_g', fs_4000: str = '4000_dps') -> None:
    """
    Method used to configure the gyroscope control register

    :param i2c: I2C object for SmartWave connection to the IMU sensor
    :param i2c_addr: Default I2C address of the ASM330LHHXG1 IMU Sensor
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


def twos_comp(val, bits: int = 16):
    """
    Compute the two's complement of the given register value

    :param val: Input data
    :param bits: Bit length
    :return: Two's complement of the input data
    """
    if (val & (1 << (bits - 1))) != 0:
        val = val - (1 << bits)
    return val


def generate_sound(frequency: int = 440, duration: float = 1, harmonics: int = 0, pitch_shift: int = 0):
    """
    Generate a sinusoidal signal from the user defined parameters
    :param frequency: Fundamental frequency of the sine wave
    :param duration: Duration of the signal in seconds
    :param harmonics: Number of harmonics to add to the signal
    :param pitch_shift: Pitch shift in octaves (positive for increase, negative for decrease)
    :return: None
    """

    fs = 44100    # Sampling frequency
    # Scale the period of the signal according to the pitch shift
    if pitch_shift < 0:
        duration = duration / (2 ** (pitch_shift * -1))

    if pitch_shift > 0:
        duration = duration * 2 ** pitch_shift

    # Generate the fundamental sine wave
    t = np.linspace(0, duration, int(fs * duration), endpoint=False)
    signal_wave = np.sin(2 * np.pi * frequency * t)

    for harmonic in range(2, harmonics + 1):
        if harmonic % 2 == 1:
            signal_wave += np.sin(2 * np.pi * frequency * harmonic * t) / harmonic

    if pitch_shift != 0:
        resample_factor = 2 ** -pitch_shift
        signal_wave = signal.resample(signal_wave, int(len(signal_wave) * resample_factor))

    return signal_wave


def main():
    """
    The main function handles the connection to SmartWave and the ASM330LHHXG1 IMU Sensor. It configures the
    accelerometer and gyroscope, sets default plotting parameters, and reads the angular and linear rate registers
    for data visualization.
    :return: None
    """
    with SmartWave().connect() as sw:
        i2c_imu_addr = 0x6a  # Default I2C address
        i2c_imu = sw.createI2CConfig("A1", "A2", int(200e3))
        imu_id = i2c_imu.readRegister(i2c_imu_addr, 0x0f.to_bytes(1, 'big'), 1)

        if IO_EXPANDER:
            i2c_io_exp_addr = 0x20
            i2c_io_exp = sw.createI2CConfig("B2", "B1", int(200e3))
            i2c_io_exp.write(i2c_io_exp_addr, [0xff, 0xff])

        # Check if connection to the target device was successful
        if (imu_id[0] == 0xff) or (imu_id[0] == 0x00):
            raise ValueError("Couldn't reach device. Terminating code.")
        else:
            print(f"Connection was successful. Device ID: {imu_id[0]:#0x}")

        # Configure the ASM330LHHXG1 IMU
        axl_conf(i2c_imu, i2c_imu_addr)
        gyro_conf(i2c_imu, i2c_imu_addr)

        # Import semify logo for plotting
        file = "semify_logo.png"
        img = Image.open(file)
        resize = img.resize((np.array(img.size) / 19).astype(int))  # / 17

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
            ax.set_ylabel("Acceleration (m/s^2)", color=sem_white)
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

            pitch_lsb = i2c_imu.readRegister(i2c_imu_addr, 0x22.to_bytes(1, 'big'), 1)
            pitch_msb = i2c_imu.readRegister(i2c_imu_addr, 0x23.to_bytes(1, 'big'), 1)
            pitch = (pitch_msb[0] << 8) + pitch_lsb[0]
            tc_pitch = twos_comp(pitch)

            roll_lsb = i2c_imu.readRegister(i2c_imu_addr, 0x24.to_bytes(1, 'big'), 1)
            roll_msb = i2c_imu.readRegister(i2c_imu_addr, 0x25.to_bytes(1, 'big'), 1)
            roll = (roll_msb[0] << 8) + roll_lsb[0]
            tc_roll = twos_comp(roll)

            yaw_lsb = i2c_imu.readRegister(i2c_imu_addr, 0x26.to_bytes(1, 'big'), 1)
            yaw_msb = i2c_imu.readRegister(i2c_imu_addr, 0x27.to_bytes(1, 'big'), 1)
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
            x_axis_lsb = i2c_imu.readRegister(i2c_imu_addr, 0x28.to_bytes(1, 'big'), 1)
            x_axis_msb = i2c_imu.readRegister(i2c_imu_addr, 0x29.to_bytes(1, 'big'), 1)
            x_axis = (x_axis_msb[0] << 8) + x_axis_lsb[0]
            tc_x_axis = twos_comp(x_axis, 16)

            y_axis_lsb = i2c_imu.readRegister(i2c_imu_addr, 0x2A.to_bytes(1, 'big'), 1)
            y_axis_msb = i2c_imu.readRegister(i2c_imu_addr, 0x2B.to_bytes(1, 'big'), 1)
            y_axis = (y_axis_msb[0] << 8) + y_axis_lsb[0]
            tc_y_axis = twos_comp(y_axis, 16)

            z_axis_lsb = i2c_imu.readRegister(i2c_imu_addr, 0x2C.to_bytes(1, 'big'), 1)
            z_axis_msb = i2c_imu.readRegister(i2c_imu_addr, 0x2D.to_bytes(1, 'big'), 1)
            z_axis = (z_axis_msb[0] << 8) + z_axis_lsb[0]
            tc_z_axis = twos_comp(z_axis, 16)

            # Linear acceleration conversion
            # convert from g to m/s^2 1 g-unit = 9.80665
            x_res = tc_x_axis * axl_sens['2g'] * 9.80665
            y_res = tc_y_axis * axl_sens['2g'] * 9.80665
            z_res = tc_z_axis * axl_sens['2g'] * 9.80665
            # print(f"X_adc: {pitch:.3f}     Y_adc: {roll:.3f}    Z_adc:: {yaw:.3f}")
            # print(f"X_a: {x_res:.3f} m/s^2    Y_a: {y_res:.3f} m/s^2   Z_a: {z_res:.3f} m/s^2\n")

            ys[0].append(x_res)
            ys[0] = ys[0][-x_len:]
            line[0].set_ydata(ys[0])

            ys[1].append(y_res)
            ys[1] = ys[1][-x_len:]
            line[1].set_ydata(ys[1])

            ys[2].append(z_res)
            ys[2] = ys[2][-x_len:]
            line[2].set_ydata(ys[2])

            if IO_EXPANDER:
                io_led_toggle(i2c_io_exp, i2c_io_exp_addr, x_res, y_res)

            if PLAY_SOUND:
                frequency = 440
                duration = 0.1

                harmonics, pitch_shift = sound_modulation(x_res, y_res)

                signal_wave = generate_sound(frequency, duration, harmonics, pitch_shift)

                p = pyaudio.PyAudio()
                stream = p.open(format=pyaudio.paFloat32,
                                channels=1,
                                rate=44100,
                                output=True)
                stream.write(signal_wave.astype(np.float32).tobytes())
                stream.stop_stream()

            return line

        anim = animation.FuncAnimation(fig, animate,
                                       fargs=(ys,),
                                       interval=1,
                                       blit=True,
                                       cache_frame_data=False)

        # plt.figimage(resize, xo=int(fig.bbox.xmax // 2) + 250, yo=int(fig.bbox.ymax) + 220)
        # plt.figimage(resize, xo=int(fig.bbox.xmax // 2) + 650, yo=int(fig.bbox.ymax) + 220)
        plt.figimage(resize, origin='upper')
        # plt.get_current_fig_manager().full_screen_toggle()
        plt.show()


if __name__ == "__main__":
    process = Process(target=main)
    process.start()
    while process.is_alive():
        if keyboard.is_pressed('q'):
            print("Terminating code.")
            process.terminate()
            break

"""
Demo script for the ASM330LHHXG1 IMU Sensor
"""

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import keyboard

from multiprocessing import Process

from SmartWaveAPI import SmartWave
from imu_conf_lib import gyro_sense, gyro_odr, gyro_fs_g, gyro_fs_125, gyro_fs_4000, axl_sens, axl_odr, axl_fs

matplotlib.use('TkAgg')
# This only required if the ffmpeg is not part of the system PATH - note that the file location might be different for other users
matplotlib.rcParams['animation.ffmpeg_path'] = r"C:\resources\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe"

# If True, a video is captured of the plotting
# If False, the data is visualized in real-time
SAVE_VIDEO = False


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


def gyro_conf(i2c, i2c_addr, odr='208Hz', fs_g='500_dps', fs_125='fs_g', fs_4000='fs_g'):
    """
    Method used to configure the gyroscope control register
    :param i2c: i2c object for SmartWave connection
    :param i2c_addr: default I2C address of the ASM330LHHXG1 IMU Sensor
    :param odr: Gyroscope output data rate selectino (in Hz)
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


# Default values, used to plot a cube in 3D plane
vertices = np.array([(-1, -1, -1), (1, -1, -1), (1, 1, -1),
                     (-1, 1, -1), (-1, -1, 1), (1, -1, 1),
                     (1, 1, 1), (-1, 1, 1)])
angles = np.linspace(-np.pi, np.pi)
edges = np.zeros(shape=(len(vertices), 3, len(angles)), dtype=np.float16)


def cube_edges(pitch, roll, yaw):
    """
    Method used for calculating the displacement of the cube, according
    to the data read out from the angular rate sensor's registers
    :param pitch: Displacement along the X axis
    :param roll: Displacement along the Y axis
    :param yaw: Displacement along the Z axis
    :return: Updated cube plane
    """
    rotation_yaw = np.array([[np.cos(yaw), -np.sin(yaw), 0],
                             [np.sin(yaw), np.cos(yaw), 0],
                             [0, 0, 1]])

    rotation_pitch = np.array([[np.cos(pitch), 0, np.sin(pitch)],
                               [0, 1, 0],
                               [-np.sin(pitch), 0, np.cos(pitch)]])

    rotation_roll = np.array([[1, 0, 0],
                              [0, np.cos(roll), -np.sin(roll)],
                              [0, np.sin(roll), np.cos(roll)]])

    # Compute the combined rotation matrix
    rotation_matrix = np.dot(rotation_yaw, np.dot(rotation_pitch, rotation_roll))

    cube_plane = []
    for i in range(len(edges)):
        rotated_vertex = np.dot(rotation_matrix, vertices[i])

        newX = rotated_vertex[0] * np.cos(roll) - rotated_vertex[2] * np.sin(roll)
        newY = rotated_vertex[1]
        newZ = rotated_vertex[2] * np.cos(roll) + rotated_vertex[0] * np.sin(roll)

        edges[i, 0] = newX
        edges[i, 1] = newY
        edges[i, 2] = newZ

    cube_plane = [[edges[0], edges[1], "green"],
                  [edges[1], edges[2], "green"],
                  [edges[2], edges[3], "green"],
                  [edges[3], edges[0], "green"],
                  [edges[0], edges[4], "blue"],
                  [edges[1], edges[5], "blue"],
                  [edges[2], edges[6], "blue"],
                  [edges[3], edges[7], "blue"],
                  [edges[4], edges[5], "red"],
                  [edges[5], edges[6], "red"],
                  [edges[6], edges[7], "red"],
                  [edges[7], edges[4], "red"]]

    return cube_plane


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

    i2c.writeRegister(
        i2c_addr,
        0x10.to_bytes(1, 'big'),
        0b00010000.to_bytes(1, 'big')
    )
    device_id = i2c.readRegister(0b1101010, 0x0f.to_bytes(1, 'big'), 1)

    # Check if connection to the target device was successful
    if device_id[0] == 0xff:
        raise ValueError("Couldn't reach device. Terminating code.")
    else:
        print(f"Connection was successful. Device ID: {device_id[0]:#0x}")

    # Configure the ASM330LHHXG1 IMU
    axl_conf(i2c, i2c_addr)
    gyro_conf(i2c, i2c_addr)

    # Default settings for plotting
    plt.rcParams["figure.figsize"] = [9.50, 7.50]
    plt.rcParams["figure.autolayout"] = True
    x_len = 200

    fig = plt.figure()
    gs = fig.add_gridspec(3, 2)
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[1, 0])
    ax3 = fig.add_subplot(gs[2, 0])
    ax4 = fig.add_subplot(gs[:, 1], projection='3d')
    ax4.view_init(azim=135, elev=30)
    ax4.disable_mouse_rotation()

    fig.suptitle("IMU - Data Visualization")
    ax1.set_title("X - axis")
    ax2.set_title("Y - axis")
    ax3.set_title("Z - axis")
    ax4.set_title("Gyroscope")
    ax4.set_xlim3d([-4.0, 4.0])
    ax4.set_xlabel('X')
    ax4.set_ylim3d([-4.0, 4.0])
    ax4.set_ylabel('Y')
    ax4.set_zlim3d([-4.0, 4.0])
    ax4.set_zlabel('Z')
    xs = list(range(0, 200))

    for ax in [ax1, ax2, ax3]:
        ax.set_ylim(-20, 20)
        ax.set_ylabel("Force (m/sqq2)")
        ax.set_xlabel("Samples")
        ax.grid()

    y1data = [0] * x_len
    y2data = [0] * x_len
    y3data = [0] * x_len
    line1, = ax1.plot(xs, y1data, lw=2)
    line2, = ax2.plot(xs, y2data, lw=2, color='r')
    line3, = ax3.plot(xs, y3data, lw=2, color='g')

    line = [line1, line2, line3]
    ys = [y1data, y2data, y3data]

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

        # Angular rate conversion - rad/s for plotting
        pitch_res = np.round((tc_pitch * gyro_sense['500_dps'] * (np.pi / 180)), 3)
        roll_res = np.round((tc_roll * gyro_sense['500_dps'] * (np.pi / 180)), 3)
        yaw_res = np.round((tc_yaw * gyro_sense['500_dps'] * (np.pi / 180)), 3)
        # print(f"Pitch: {tc_pitch:.3f}     Roll: {tc_roll:.3f}    Yaw: {tc_yaw:.3f}")
        # print(f"Pitch: {pitch_res:.3f} rad/s    Roll: {roll_res:.3f} rad/s   Yaw: {yaw_res:.3f} rad/s\n")

        # Update cube orientation
        cube_plane = cube_edges(pitch_res, roll_res, yaw_res)

        all_lines = []

        # Clear previous cube plot
        for cube_line in ax4.lines:
            cube_line.set_data([], [])
            cube_line.set_3d_properties([])

        # Plot the cube edges
        for vertex in cube_plane:
            line_c = ax4.plot([vertex[0][0][0], vertex[1][0][0]],
                              [vertex[0][1][0], vertex[1][1][0]],
                              [vertex[0][2][0], vertex[1][2][0]],
                              vertex[2])
            all_lines.append(line_c[0])

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

        ys[0].append(x_res)
        ys[0] = ys[0][-x_len:]
        line[0].set_ydata(ys[0])

        ys[1].append(y_res)
        ys[1] = ys[1][-x_len:]
        line[1].set_ydata(ys[1])

        ys[2].append(z_res)
        ys[2] = ys[2][-x_len:]
        line[2].set_ydata(ys[2])

        return line, all_lines

    if SAVE_VIDEO:
        anim = animation.FuncAnimation(fig, animate,
                                       fargs=(ys,),
                                       interval=1,
                                       repeat=True,
                                       save_count=5000
                                       )

        file_loc = r"C:/semify/Git/wfg-API/examples/imu.mp4"
        write_vid = animation.FFMpegWriter(fps=10, extra_args=['-vcodec', 'libx264'])
        anim.save(file_loc, writer=write_vid)

    else:
        # If blit set to False, the cube gets updated real-time, but the animation becomes very slow
        # If blit is set to True, the cube won't be plotted along with the accelerometer data.
        # This requires the animate function to be modified to only return line
        anim = animation.FuncAnimation(fig, animate,
                                       fargs=(ys,),
                                       interval=1,
                                       blit=False,
                                       cache_frame_data=False)

        plt.show()
    sw.disconnect()


if __name__ == "__main__":
    process = Process(target=main)
    process.start()
    while process.is_alive():
        if keyboard.is_pressed('q'):
            process.terminate()
            break

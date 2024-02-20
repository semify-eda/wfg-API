from SmartWaveAPI import SmartWave, GPIO
import time

def main():
    with SmartWave().connect() as sw:
        with sw.createGPIO() as gpio:
            print("oida")
            time.sleep(1)


if __name__ == '__main__':
    main()
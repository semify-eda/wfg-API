from SmartWaveAPI import SmartWave
import time

def main():
    with SmartWave().connect() as sw:
        sw.updateFPGABitstream()


if __name__ == "__main__":
    main()
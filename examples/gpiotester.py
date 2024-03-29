from SmartWaveAPI import SmartWave
from SmartWaveAPI.definitions import PinOutputType
from SmartWaveAPI.configitems import GPIO
import time

def main():
    with SmartWave().connect() as sw:
        with sw.createGPIO(input_level_callback=lambda x: print("InputA: %d" % x), output_type=PinOutputType.PushPull) as gpioA:
            with sw.createGPIO(pin_name="B1", input_level_callback=lambda x: print("InputB: %d" % x), name="GPIOB") as gpioB:
                input()
                print("A1")
                gpioA.level = 1

                input()
                print("A0")
                gpioA.level = 0
                gpioA.name = "GPIOA"

                input()
                gpioA.outputType = PinOutputType.PushPull

                input()
                print("A1")
                gpioA.level = 1

                input()
                print("A0")
                gpioA.level = 0
                print("Alevel", gpioA.inputLevel)

                input()
                print("pullup A")
                gpioA.pullup = True


                input()
                print("A1")
                gpioA.level = 1

                input()
                print("A0")
                gpioA.level = 0

                input()
                print("noOutA")
                gpioA.outputType = PinOutputType.Disable

                input()
                print("pullupB")
                gpioB.pullup = True

                input()
                print("noPullup")
                gpioA.pullup = False
                gpioB.pullup = False

                input()
                print("A open drain")
                gpioA.outputType = PinOutputType.OpenDrain

                input()
                print("A low")
                gpioA.level = 0

                input()
                print("A high")
                gpioA.level = 1

                # input()
                # print("A low")
                # gpioA.level = 0

                input()
                print("no pullups")
                gpioA.pullup = False
                gpioB.pullup = False


                input()
                print("A high")
                gpioA.level = 1

                input()
                print("A low")
                gpioA.level = 0

                input()
                print("B pushpull")
                gpioB.outputType = PinOutputType.PushPull

                input()
                print("A0B0")
                gpioA.level = 0
                gpioB.level = 0

                input()
                print("A0B1")
                gpioA.level = 0
                gpioB.level = 1

                input()
                print("A1B0")
                gpioA.level = 1
                gpioB.level = 0


                input()
                print("A1B1")
                gpioA.level = 1
                gpioB.level = 1

                input()

if __name__ == '__main__':
    main()

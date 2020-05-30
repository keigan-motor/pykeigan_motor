import msvcrt
from time import sleep

current_dir = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir) + '/../../') # give 1st priority to the directory where pykeigan exists

from pykeigan import usbcontroller
from pykeigan import utils

# Select port connecting to KeiganMotor
port = 'COM7'
dev = usbcontroller.USBController(port)


if __name__ == '__main__':
    try:
        while True:
            sleep(0.01)
            if msvcrt.kbhit():
                c = msvcrt.getwch()
                print(c)

                if c == 'r':
                    # rpm -> radian/sec
                    dev.enable_action()
                    dev.set_speed(utils.rpm2rad_per_sec(5))
                    dev.set_led(1, 0, 200, 0)
                    dev.run_forward()
                elif c == 's':
                    dev.stop_motor()

    except KeyboardInterrupt:
        if dev:
            dev.disable_action()
        print('Ctrl-C')

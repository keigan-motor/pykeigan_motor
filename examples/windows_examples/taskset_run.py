import msvcrt
from time import sleep

current_dir = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir) + '/../../') # give 1st priority to the directory where pykeigan exists

from pykeigan import usbcontroller
from pykeigan import utils

# How to use (this sample was made for Windows) 
# (this sample was made for Windows) 
#
# (1) Define port 'COM?' that connected to KeiganMotor (You can see by DeviceManager)
# (2) Set index to record and do taskset (selectable from 0 to 49)
# (3) Set repeat to repeat when doing taskset (0~, 0 will repeat infinitely)
# (4) Excute this file
# (5) Press 'r' to record my_taskset in KeiganMotor
# (6) Press 'd' to do taskset

# Select port connecting to KeiganMotor
port = 'COM7'
dev = usbcontroller.USBController(port)

index = 0 # index to record and do taskset
repeat = 1 # repeating number to do taskset

# Edit this function to record your taskset
# (Recorded in KeiganMotor)
def my_taskset():
    dev.set_speed(utils.rpm2rad_per_sec(5))
    dev.set_led(1, 0, 200, 0)
    dev.run_forward()
    dev.wait_queue(5000) # wait for 5000 ms
    dev.stop_motor()

def record_taskset():
    dev.erase_taskset(index)
    sleep(0.5)
    dev.start_recording_taskset(index)
    my_taskset()
    dev.stop_recording_taskset()

def do_taskset():
    dev.enable_action()
    dev.start_doing_taskset(index, repeat)


if __name__ == '__main__':
    try:
        while True:
            sleep(0.01)
            if msvcrt.kbhit():
                c = msvcrt.getwch()
                # print(c)

                if c == 'r':
                    print('Record taskset index: %d' % index)
                    record_taskset()

                elif c == 'd':
                    print('Do taskset index: %d, repeat: %d', index, repeat)
                    do_taskset() 

    except KeyboardInterrupt:
        if dev:
            dev.disable_action()
        print('Ctrl-C')

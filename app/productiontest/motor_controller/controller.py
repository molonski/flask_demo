import os
import gclib
import time
from yaml import load, Loader


class Controller(object):
    """
    Artiphon Production Motor Controller Functions

    Attributes:
        x: current position (mm) of x axis motor driver
        y: current position (mm) of y axis motor driver
        z: current position (mm) of z axis motor driver
        ef: current position (mm) of end effector axis motor driver

    """

    def __init__(self):
        self.config = load(open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'local_config.yaml'),
                                'rb'), Loader=Loader)

        self.g = gclib.py()
        self.open()

        self.x = 0
        self.x_counts = 0
        x_config = self.config['servos']['x']
        self.x_motor = x_config['motor_name']
        self.x_mm_per_count = x_config['pitch'] / x_config['steps_per_revolution'] / x_config ['step_down']

        self.y = 0
        self.y_counts = 0
        y_config = self.config['servos']['y']
        self.y_motor = y_config['motor_name']
        self.y_mm_per_count = y_config['pitch'] / y_config['steps_per_revolution'] / y_config['step_down']

        self.z = 0
        self.z_counts = 0
        z_config = self.config['servos']['z']
        self.z_motor = z_config['motor_name']
        self.z_mm_per_count = z_config['pitch'] / z_config['steps_per_revolution'] / z_config['step_down']

        # the end effector is a voice coil not an stepper motor
        self.ef_motor = self.config['ef']['motor_name']
        self.ef_up_voltage = self.config['ef']['up']
        self.ef_down_voltage = self.config['ef']['down']

    def open(self):
        usb_ids = os.popen("ls /dev/tty.usbserial-0*").read().split('\n')

        for usb_id in usb_ids:
            try:
                self.g.GOpen('{} --direct'.format(usb_id))
                break
            except gclib.GclibError:
                pass

    def connection_info(self):
        return self.g.GInfo()

    def initialize_motor_controller(self):
        c = self.g.GCommand

        # for XY homing routine
        c('CN , {}'.format(self.config['globals']['CN']))    # set home motor direction
        c('HV '.format(self.config['globals']['HV']))        # set home back off speed

        # Y axis motor has a internal Galil sine drive we don't want to use
        c('BR 1,-1')

        # Set up voice coil actuation - recommendations from Kushal in Mar 22 2019 to Neal
        # first PID gains to zero
        c('KP{}={}'.format(self.ef_motor, self.config['ef']['KP']))
        c('KD{}={}'.format(self.ef_motor, self.config['ef']['KD']))
        c('KI{}={}'.format(self.ef_motor, self.config['ef']['KI']))

        # second motor off to set amplifier gain
        c('MO{}'.format(self.ef_motor))  # turn motor off to set Amplifier Gain to 0
        c('AG {}'.format(self.config['ef']['AG']))
        c('SH{}'.format(self.ef_motor))  # turn motor on again

        # third set torque limit, 3V volts limits to 1.2 Amps max current
        c('TL{}={}'.format(self.ef_motor, self.config['ef']['TL']))

        # lift the voice coil actuator
        c('OF{}={}'.format(self.ef_motor, self.ef_up_voltage))

    def close(self):
        c = self.g.GCommand

        self.position_tracking_mode(on=False)

        # remove voice coil voltage
        c('OF{}=0'.format(self.ef_motor))

        # stop and turn off all motors
        c('ST')
        c('MO')

        self.g.GClose()

        self.g = None

    def set_motor_speed(self, axis, mm_per_second):
        """

        :param axis: string - x, y, z, ef
        :param mm_per_second: int or float - mm/s
        :return: none
        """
        c = self.g.GCommand

        motor_config = self.config['servos'][axis]

        mm_per_count = motor_config['pitch'] / motor_config['steps_per_revolution'] / motor_config['step_down']

        c('SH{}'.format(motor_config['motor_name']))

        c('SP{}={}'.format(motor_config['motor_name'], mm_per_second / mm_per_count))

    def zero_xy_position(self):
        # route commands to
        c = self.g.GCommand

        # ====================================
        # move axes one at a time

        for axis, motor in [('x', self.x_motor), ('y', self.y_motor)]:
            # set the servos to use
            c('SH{}'.format(motor))

            # reduce the speed
            self.set_motor_speed(axis, self.config['globals']['homing_speed'])

            # issue Home Command
            c('HM{}'.format(motor))
            c('BG{}'.format(motor))

            # wait for motion to complete
            self.g.GMotionComplete('{}'.format(motor))

            # issue short wait
            time.sleep(0.25)

        # zero current position
        self.x = 0
        self.y = 0

        self.x_counts = 0
        self.y_counts = 0

    def zero_z_position(self):
        # route commands to
        c = self.g.GCommand

        # set the servos to use
        c('SH{}'.format(self.z_motor))

        # reduce the speed
        self.set_motor_speed('z', self.config['globals']['homing_speed'])

        # issue Home Command
        c('PR{}=-{}'.format(self.z_motor, self.config['servos']['z']['range']))
        c('BG{}'.format(self.z_motor))

        # wait for motion to complete
        self.g.GMotionComplete('{}'.format(self.z_motor))

        # issue short wait
        time.sleep(0.25)

        # zero current position
        c('DP{}=0'.format(self.z_motor))    # DP - define position to set zero for Position Absolute commands
        self.z = 0
        self.z_counts = 0

    def position_tracking_mode(self, on=True):
        c = self.g.GCommand
        if on:
            c('PT 0, 1, 1, 1')  # A = voice coil => always off
        else:
            c('PT 0, 0, 0, 0')

    def update_z_position(self, next_z=None):
        # actuate the Z direction before the XY directions so the end effector is not accidentally broken

        c = self.g.GCommand

        # convert next_z to counts and move to absolute position
        c('PA{}={}'.format(self.z_motor, next_z / self.z_mm_per_count))

        self.g.GMotionComplete('{}'.format(self.z_motor))

        # update current positions
        self.z = next_z
        self.z_counts = next_z / self.z_mm_per_count

    def update_xy_position(self, next_x=None, next_y=None):
        # actuate the Z direction before the XY directions so the end effector is not accidentally broken

        if abs(next_x) > abs(self.config['globals']['max_x']):
            raise Exception('X coordinate exceeds table dimension of {} mm'.format(abs(self.config['globals']['max_x'])))
        if abs(next_y) > abs(self.config['globals']['max_y']):
            raise Exception('Y coordinate exceeds table dimension of {} mm'.format(abs(self.config['globals']['max_y'])))

        c = self.g.GCommand

        # convert next positions to counts and move to absolute position
        c('PA{}={}'.format(self.x_motor, next_x / self.x_mm_per_count))
        c('PA{}={}'.format(self.y_motor, next_y / self.y_mm_per_count))

        self.g.GMotionComplete('{}{}'.format(self.x_motor, self.y_motor))

        # update current positions
        self.x = next_x
        self.y = next_y
        self.x_counts = next_x / self.x_mm_per_count
        self.y_counts = next_y / self.y_mm_per_count

    def actuate_end_effector(self, voltage):
        # ideal operating range is 5 - 15 mm of extension for consistent force application
        # end effector should be at least 5 mm away from target before extended in order
        # to get consistent results in spite of slight distance variations
        # see voice coil documentation
        # http://moticont.com/pdf/GVCM-025-038-02.pdf

        c = self.g.GCommand

        c('OF{}={}'.format(self.ef_motor, voltage))

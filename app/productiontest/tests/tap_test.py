import time
import datetime
import numpy as np
from app.productiontest.motor_controller import controller
from app.productiontest.constants import *
from app.productiontest.tests.result_check import result_check


class TapTest(object):
    """
    Tap test routine for instruments

    """

    def __init__(self, logger, tp, instrument=None):

        self.logger = logger
        self.test_plan = tp
        self.instrument = instrument

        self.logger.info('attempting to connect to motor controller...')
        # load motor controller
        try:
            self.mc = controller.Controller()
            self.logger.info('motor controller connected: {}'.format(self.mc.connection_info()))
            self.mc_connected = True
        except Exception as e:
            self.logger.error("Exception during motor controller initialization.", exc_info=True)
            self.logger.error("Aborting tap test routine.")
            self.mc_connected = False

    def perform_test(self, step_through=True):
        # try, except, finally to make sure motor controller is shutdown properly
        try:
            self.logger.info('Beginning Tap Test...')

            # determine the indices of test plan that apply to the tap test
            df_tt = self.test_plan[(self.test_plan[TEST_TYPE_OR_COMPONENT] == 'tap_test') &
                                   (self.test_plan[MEASUREMENT_TYPE] == SENSOR_IDENTIFIER)]
            df_tt = df_tt.sort_values(by=[SORT_COL]) if SORT_COL in df_tt.columns else df_tt
            test_order = df_tt.index

            # initial motor controller
            self.mc.initialize_motor_controller()

            # zero the motor positions
            self.logger.info('zeroing X and Y motor positions.')
            self.mc.zero_xy_position()
            self.logger.info('zeroing Z motor positions.')
            self.mc.zero_z_position()

            # turning on Position Tracking Mode
            self.mc.position_tracking_mode(on=True)

            # default operating speed from config
            mm_per_second = self.mc.config['globals']['operating_speed']

            # set the motor speed to operating speed and log
            self.logger.info('setting translation speeds to {} mm/s'.format(mm_per_second))
            for axis in ['x', 'y', 'z']:
                self.mc.set_motor_speed(axis, mm_per_second=mm_per_second)

            # end effector voltage list
            # multiple force responses will be collected at each sensor
            v_up = self.mc.ef_up_voltage
            v_down = self.mc.ef_down_voltage
            v_step = v_down / float(FORCE_STEPS)
            v_range = [round(v, 5) for v in np.arange(0, v_down + v_step, v_step).tolist() + [v_up]]

            self.logger.info('starting tap test routine')
            for m_ind in test_order:

                self.logger.info('moving to position: ({} mm, {} mm, {} mm)'.format(self.test_plan.loc[m_ind, X_COL],
                                                                                    self.test_plan.loc[m_ind, Y_COL],
                                                                                    self.test_plan.loc[m_ind, Z_COL]))

                # coordinates of next measurement
                next_x = self.test_plan.loc[m_ind, X_COL]
                next_y = self.test_plan.loc[m_ind, Y_COL]
                next_z = self.test_plan.loc[m_ind, Z_COL]

                # consider change in Z direction before making the position change
                # if Z is increasing, then move z first, if z is decreasing then move XY first
                # this is to prevent the end effector from getting hung up on instrument geometry
                # the motors could bend or brake the voice coil plunger
                if next_z - self.mc.z > 0:
                    # going up = z first
                    self.mc.update_z_position(next_z=next_z)
                    self.mc.update_xy_position(next_x=next_x, next_y=next_y)
                else:
                    # going down, or no z change = xy first
                    self.mc.update_xy_position(next_x=next_x, next_y=next_y)
                    if next_z - self.mc.z < 0:
                        # only call z change if needed
                        self.mc.update_z_position(next_z=next_z)

                self.logger.info('taking measurement: {}'.format(self.test_plan.loc[m_ind, MEASUREMENT_NAME]))

                force_scale = self.test_plan.loc[m_ind, FORCE_SCALE]

                self.logger.info('sensor serial name: {}'.format(self.test_plan.loc[m_ind, MEASUREMENT_DEV_NAME]))

                # for v_ind, voltage in enumerate(v_range):

                # apply voltage
                # remove upward pull on end effector
                self.mc.actuate_end_effector(0)
                # time.sleep(0.1)
                # # apply light downward force to move position, but prevent a slam into instrument
                # self.mc.actuate_end_effector(0.25)
                # time.sleep(0.1)
                # apply full force
                self.mc.actuate_end_effector(v_range[-2] * force_scale)
                time.sleep(2)

                readings = []
                # take readings
                if self.instrument:

                    # if reading is a failure then take another reading after a short delay
                    for read_ind in range(5):

                        sensor_reading = self.instrument.read_sensor(self.test_plan.loc[m_ind, MEASUREMENT_DEV_NAME])

                        readings.append(sensor_reading)

                        self.logger.info('\treading: {}'.format(sensor_reading))

                        pass_fail = result_check(self.test_plan.loc[m_ind, COMPARISON_TYPE],
                                                 self.test_plan.loc[m_ind, MIN_ALLOW],
                                                 self.test_plan.loc[m_ind, MAX_ALLOW],
                                                 self.test_plan.loc[m_ind, MEASUREMENT])

                        if pass_fail == 'pass':
                            break
                        elif read_ind == 4:
                            pass
                        else:
                            time.sleep(0.25)

                    # put max reading in measurement column
                    self.test_plan.loc[m_ind, MEASUREMENT] = max(readings)
                    self.test_plan.loc[m_ind, TIMESTAMP] = datetime.datetime.utcnow()

                    # capture the full range of values taken
                    self.test_plan.loc[m_ind, TX] = ''  # , '.join([str(round(v * force_scale, 6)) for v in v_range])
                    self.test_plan.loc[m_ind, TY] = ''  # , '.join([str(np.round(r, 6)) for r in readings])

                    # check pass / fail result
                    self.test_plan.loc[m_ind, PASS_FAIL] = pass_fail

                # log result
                self.logger.info('{} - {} - {}'.format(self.test_plan.loc[m_ind, MEASUREMENT_NAME],
                                                       self.test_plan.loc[m_ind, MEASUREMENT],
                                                       self.test_plan.loc[m_ind, PASS_FAIL]))

                self.mc.actuate_end_effector(v_range[-1])

                if step_through:
                    # wait for keyboard input
                    resp = input()
                    if resp.lower() == 'break':
                        break
                    elif resp.lower() in ['false', 'continue']:
                        step_through = False

            self.logger.info('tap test routine completed successfully')

            # zero the motor positions
            self.logger.info('zeroing X and Y motor positions.')
            self.mc.zero_xy_position()


        except Exception as e:
            self.logger.error("Exception during test routine.", exc_info=True)
            self.logger.error("Aborted tap test routine.")

        finally:
            self.mc.close()

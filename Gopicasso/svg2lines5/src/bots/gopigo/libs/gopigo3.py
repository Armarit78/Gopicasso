# https://www.dexterindustries.com/GoPiGo/
# https://github.com/DexterInd/GoPiGo3
#
# Copyright (c) 2017 Dexter Industries
# Released under the MIT license (http://choosealicense.com/licenses/mit/).
# For more information see https://github.com/DexterInd/GoPiGo3/blob/master/LICENSE.md
#
# Python drivers for the GoPiGo3

from __future__ import print_function
from __future__ import division
#from builtins import input
hardware_connected = True
__version__ = "1.3.2"

import subprocess # for executing system calls

import math       # import math for math.pi constant
import time
import json

FIRMWARE_VERSION_REQUIRED = "1.0.x" # Make sure the top 2 of 3 numbers match


class Enumeration(object):
    def __init__(self, names):  # or *names, with no .split()
        number = 0
        for _, name in enumerate(names.split('\n')):
            if name.find(",") >= 0:
                # strip out the spaces
                while(name.find(" ") != -1):
                    name = name[:name.find(" ")] + name[(name.find(" ") + 1):]

                # strip out the commas
                while(name.find(",") != -1):
                    name = name[:name.find(",")] + name[(name.find(",") + 1):]

                # if the value was specified
                if(name.find("=") != -1):
                    number = int(float(name[(name.find("=") + 1):]))
                    name = name[:name.find("=")]

                # optionally print to confirm that it's working correctly
                #print "%40s has a value of %d" % (name, number)

                setattr(self, name, number)
                number = number + 1


class FirmwareVersionError(Exception):
    """Exception raised if the GoPiGo3 firmware needs to be updated"""


class SensorError(Exception):
    """Exception raised if a sensor is not yet configured when trying to read it"""


class I2CError(Exception):
    """Exception raised if there was an error on an I2C bus"""


class ValueError(Exception):
    """Exception raised if trying to read an invalid value"""


class GoPiGo3(object):
    WHEEL_BASE_WIDTH         = 117  # distance (mm) from left wheel to right wheel. This works with the initial GPG3 prototype. Will need to be adjusted.
    WHEEL_DIAMETER           = 66.5 # wheel diameter (mm)
    WHEEL_BASE_CIRCUMFERENCE = WHEEL_BASE_WIDTH * math.pi # The circumference of the circle the wheels will trace while turning (mm)
    WHEEL_CIRCUMFERENCE      = WHEEL_DIAMETER   * math.pi # The circumference of the wheels (mm)

    MOTOR_GEAR_RATIO           = 120 # Motor gear ratio # 220 for Nicole's prototype
    ENCODER_TICKS_PER_ROTATION = 6   # Encoder ticks per motor rotation (number of magnet positions) # 16 for early prototypes
    MOTOR_TICKS_PER_DEGREE = ((MOTOR_GEAR_RATIO * ENCODER_TICKS_PER_ROTATION) / 360.0) # encoder ticks per output shaft rotation degree

    MOTOR_LEFT  = 0x01
    MOTOR_RIGHT = 0x02

    MOTOR_FLOAT = -128

    BOT = None

    def __init__(self, addr = 8, detect = True, config_file_path="/home/pi/Dexter/gpg3_config.json"):
        """
        Do any necessary configuration, and optionally detect the GoPiGo3

        * Optionally set the SPI address to something other than 8
        * Optionally disable the detection of the GoPiGo3 hardware. This can be used for debugging
          and testing when the GoPiGo3 would otherwise not pass the detection tests.

        The ``config_file_path`` parameter represents the path to a JSON file. The presence of this configuration file is optional and is only required in cases where
        the GoPiGo3 has a skewed trajectory due to minor differences in these two constants: the **wheel diameter** and the **wheel base width**. In most cases, this won't be the case.

        By-default, the constructor tries to read the ``config_file_path`` file and silently fails if something goes wrong: wrong permissions, non-existent file, improper key values and so on.
        To set custom values to these 2 constants, use :py:meth:`~easygopigo3.EasyGoPiGo3.set_robot_constants` method and for saving the constants to a file call
        :py:meth:`~easygopigo3.EasyGoPiGo3.save_robot_constants` method.

        """

        import builtins
        self.BOT = builtins.EMULATED_BOT

        class GoPiGo3Motors:
            def __init__(self, motors: list) -> None:
                self.motors = motors

            def set_position(self, degrees: float) -> None:
                for m in self.motors: m.set_position(degrees)

            def set_limits(self, dps: float) -> None:
                for m in self.motors: m.set_limits(dps)

            def set_dps(self, dps: float) -> None:
                for m in self.motors: m.set_dps(dps)

            def set_power(self, power: int) -> None:
                for m in self.motors: m.set_power(power)

            def offset_encoder(self, degrees: float) -> None:
                for m in self.motors: m.offset_encoder(degrees)

        self.MOTORS = [None, self.BOT.left_motor, self.BOT.right_motor, GoPiGo3Motors([self.BOT.left_motor, self.BOT.right_motor])]


    def set_robot_constants(self, wheel_diameter, wheel_base_width, ticks, motor_gear_ratio):
        """
        Set new wheel diameter and wheel base width values for the GoPiGo3.

        :param float wheel_diameter: Diameter of the GoPiGo3 wheels as measured in millimeters.
        :param float wheel_base_width: The distance between the 2 centers of the 2 wheels as measured in millimeters.

        This should only be required in rare cases when the GoPiGo3's trajectory is skewed due to minor differences in the wheel-to-body measurements.

        The GoPiGo3 class instantiates itself with default values for both constants:

        1. ``wheel_diameter`` is by-default set to **66.5** *mm*.

        2. ``wheel_base_width`` is by-default set to **117** *mm*.

        3. ``ticks`` is by default set to **6**, but GoPiGos manufactured in 2021 need 16.

        4. ``motor_gear_ratio`` is by default set to **120**.

        """
        self.WHEEL_DIAMETER = wheel_diameter
        self.WHEEL_CIRCUMFERENCE = self.WHEEL_DIAMETER * math.pi
        self.WHEEL_BASE_WIDTH = wheel_base_width
        self.WHEEL_BASE_CIRCUMFERENCE = self.WHEEL_BASE_WIDTH * math.pi
        self.MOTOR_GEAR_RATIO = motor_gear_ratio
        self.ENCODER_TICKS_PER_ROTATION = ticks
        self.MOTOR_TICKS_PER_DEGREE = ((self.MOTOR_GEAR_RATIO * self.ENCODER_TICKS_PER_ROTATION) / 360.0)

    def get_id(self):
        """
        Read the 128-bit GoPiGo3 hardware serial number

        Returns touple:
        serial number as 32 char HEX formatted string, error
        """
        return "00000000000000000000000000000000"

    def set_led(self, led, red, green = 0, blue = 0):
        """
        Set an LED

        Keyword arguments:
        led -- The LED(s). LED_LEFT_EYE, LED_RIGHT_EYE, LED_LEFT_BLINKER, LED_RIGHT_BLINKER, and/or LED_WIFI.
        red -- The LED's Red color component (0-255)
        green -- The LED's Green color component (0-255)
        blue -- The LED's Blue color component (0-255)
        """

        if led < 0 or led > 255:
            return

        if red > 255:
            red = 255
        if green > 255:
            green = 255
        if blue > 255:
            blue = 255

        if red < 0:
            red = 0
        if green < 0:
            green = 0
        if blue < 0:
            blue = 0

        print("set_led() called")
        # TODO

    def get_voltage_5v(self):
        """
        Get the 5v circuit voltage

        Returns touple:
        5v circuit voltage, error
        """
        value = 4800 #self.spi_read_16(self.SPI_MESSAGE_TYPE.GET_VOLTAGE_5V)
        return (value / 1000.0)

    def get_voltage_battery(self):
        """
        Get the battery voltage

        Returns touple:
        battery voltage, error
        """
        value = 4900 #self.spi_read_16(self.SPI_MESSAGE_TYPE.GET_VOLTAGE_VCC)
        return (value / 1000.0)

    def set_servo(self, servo, us):
        """
        Set a servo position in microseconds

        Keyword arguments:
        servo -- The servo(s). SERVO_1 and/or SERVO_2.
        us -- The pulse width in microseconds (0-16666)
        """
        print("set_servo() called")
        # TODO

    def set_motor_power(self, port, power):
        """
        Set the motor power in percent

        Keyword arguments:
        port -- The motor port(s). MOTOR_LEFT and/or MOTOR_RIGHT.
        power -- The PWM power from -100 to 100, or MOTOR_FLOAT for float.
        """
        if(power > 127):
            power = 127
        if(power < -128):
            power = -128
        self.MOTORS[port].set_power(power)

    def set_motor_position(self, port, position):
        """
        Set the motor target position in degrees

        Keyword arguments:
        port -- The motor port(s). MOTOR_LEFT and/or MOTOR_RIGHT.
        position -- The target position
        """
        self.MOTORS[port].set_position(position)

    def set_motor_dps(self, port, dps):
        """
        Set the motor target speed in degrees per second

        Keyword arguments:
        port -- The motor port(s). MOTOR_LEFT and/or MOTOR_RIGHT.
        dps -- The target speed in degrees per second
        """
        self.MOTORS[port].set_dps(dps)

    def set_motor_limits(self, port, power = 0, dps = 0):
        """
        Set the motor speed limit

        Keyword arguments:
        port -- The motor port(s). MOTOR_LEFT and/or MOTOR_RIGHT.
        power -- The power limit in percent (0 to 100), with 0 being no limit (100)
        dps -- The speed limit in degrees per second, with 0 being no limit
        """
        self.MOTORS[port].set_limits(dps)

    def get_motor_status(self, port):
        """
        Read a motor status

        Keyword arguments:
        port -- The motor port (one at a time). MOTOR_LEFT or MOTOR_RIGHT.

        Returns a list:
            flags -- 8-bits of bit-flags that indicate motor status:
                bit 0 -- LOW_VOLTAGE_FLOAT - The motors are automatically disabled because the battery voltage is too low
                bit 1 -- OVERLOADED - The motors aren't close to the target (applies to position control and dps speed control).
            power -- the raw PWM power in percent (-100 to 100)
            encoder -- The encoder position
            dps -- The current speed in Degrees Per Second
        """
        if port == self.MOTOR_LEFT:
            pass #message_type = self.SPI_MESSAGE_TYPE.GET_MOTOR_STATUS_LEFT
        elif port == self.MOTOR_RIGHT:
            pass #message_type = self.SPI_MESSAGE_TYPE.GET_MOTOR_STATUS_RIGHT
        else:
            raise IOError("get_motor_status error. Must be one motor port at a time. MOTOR_LEFT or MOTOR_RIGHT.")
            return

        return self.MOTORS[port].get_status()

    def get_motor_encoder(self, port):
        """
        Read a motor encoder in degrees

        Keyword arguments:
        port -- The motor port (one at a time). MOTOR_LEFT or MOTOR_RIGHT.

        Returns the encoder position in degrees
        """
        if port == self.MOTOR_LEFT:
            pass #message_type = self.SPI_MESSAGE_TYPE.GET_MOTOR_ENCODER_LEFT
        elif port == self.MOTOR_RIGHT:
            pass #message_type = self.SPI_MESSAGE_TYPE.GET_MOTOR_ENCODER_RIGHT
        else:
            raise IOError("Port(s) unsupported. Must be one at a time.")
            return 0

        return self.MOTORS[port].get_encoder()

    def offset_motor_encoder(self, port, offset):
        """
        Offset a motor encoder

        Keyword arguments:
        port -- The motor port(s). MOTOR_LEFT and/or MOTOR_RIGHT.
        offset -- The encoder offset

        Zero the encoder by offsetting it by the current position
        """
        self.MOTORS[port].offset_encoder(offset)

    def reset_motor_encoder(self, port):
        """
        Reset a motor encoder to 0

        Keyword arguments:
        port -- The motor port(s). MOTOR_LEFT and/or MOTOR_RIGHT.
        """
        if port & self.MOTOR_LEFT:
            self.offset_motor_encoder(self.MOTOR_LEFT, self.get_motor_encoder(self.MOTOR_LEFT))

        if port & self.MOTOR_RIGHT:
            self.offset_motor_encoder(self.MOTOR_RIGHT, self.get_motor_encoder(self.MOTOR_RIGHT))

    def reset_all(self):
        """
        Reset the GoPiGo3.
        """

        # Turn off the motors
        self.set_motor_power(self.MOTOR_LEFT + self.MOTOR_RIGHT, self.MOTOR_FLOAT)

        # Reset the motor limits
        self.set_motor_limits(self.MOTOR_LEFT + self.MOTOR_RIGHT, 0, 0)

        # Turn off the servos
        self.set_servo(self.SERVO_1 + self.SERVO_2, 0)

        # Turn off the LEDs
        self.set_led(self.LED_EYE_LEFT + self.LED_EYE_RIGHT + self.LED_BLINKER_LEFT + self.LED_BLINKER_RIGHT, 0, 0, 0)

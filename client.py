import os
import sys
import time
import smbus
import pigpio
import signal
import requests
import numpy as np
import RPi.GPIO as GPIO

#Instructions:
#Execute: "sudo pigpiod" when using pins for PWM
#See Main section below for arguments that could be passed


#######################################################
#CLIENT: Controls communication to server and output on GPIO pins
#######################################################

class Client:
    URL = 'https://dimmerbrightness.herokuapp.com/'
    # Using BCM modes
    PINS_IN =[6, 13, 19, 26, 16, 20, 21]
    PINS_OUT = [17, 27, 22, 23]  

    def __init__(self, debug, nolux, digital):
        self.debug = debug
        self.nolux = nolux
        self.digital = digital
        self.server_input = {}
        self.setup_gpio()
        self.pwm_values = []
        if not self.digital:
            self.pwm_reader = PWM_Reader(pigpio.pi(), 5)

    # Setup input and output pins
    def setup_GPIO(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(Client.PINS_OUT, GPIO.OUT)
        if self.digital:
            GPIO.setup(Client.PINS_IN, GPIO.IN)
        return

    # Send data to server
    def send(self):
        try:
            response = requests.post(Client.URL, self.server_input)                        
        except requests.exceptions.ConnectionError:
            print("Warning: Failed sending data to server, trying again.")
            response = self.send()
        assert response.status_code == 200
        return response

    # Start client to:
    #       read lux sensor
    #       send to server
    #       receive LED brightness from server
    #       change output on pins according to brightness
    def start(self):
        lux_value = -1
        while True:
            if not self.nolux:
                lux_value = '{:0.2f}'.format(self.read_lux_sensor())
            self.log("lux_sensor: " + str(lux_value))
            # set data to be send to server
            self.server_input['lux_sensor_value'] = lux_value
            self.server_input['power'] = self.read_power()
            response = self.send()
            led_brightness = response.text
            self.log("Intensity: " + led_brightness)
            self.set_led_brightness(led_brightness)
            time.sleep(1)
        return

    # Change output on GPIO pins according to brightness
    def set_led_brightness(self, led_brightness):
        # Given the led brightness percentage as a string will
        # convert it to the corresponding binary to set the GPIO pins
        binary = "{0:b}".format(int(led_brightness)//10)
        if len(binary) != 4: binary = (4-len(binary))*'0'+binary
        self.log("GPIO Pins: " + binary)

        # change output on pins
        for i in range(len(Client.PINS_OUT)):
            if int(binary[i]) == 1:
                    GPIO.output(Client.PINS_OUT[i], GPIO.HIGH)
            else:
                    GPIO.output(Client.PINS_OUT[i], GPIO.LOW)
        return

    # Read power on GPIO pins
    def read_power(self):
        # Read pins as digital
        if self.digital:
            power_Binary=""
            for i in range(len(Client.PINS_IN)):
                power_Binary += str(GPIO.input(Client.PINS_IN[i]))
            self.log("Input Digital Input pins: " + power_Binary)
            return str(int(power_Binary,2))

        # Read PWM from pin
        pwmReadingValue = int(round(self.pwm_reader.duty_cycle()))
        if(len(self.pwm_values) == 0):
            mean = 500  # arbitrary value
        else:
            mean = np.mean(self.pwm_values)
        # Try to even out slight noise in reading
        if abs(mean - pwmReadingValue) <= 2:
            pwmReadingValue = self.pwm_values[-1]
            self.pwm_values.append(pwmReadingValue)
            if len(self.pwm_values) > 5:
                self.pwm_values.pop(0)
        # There is a huge different, possibly PWM changed
        else:
            self.pwm_values = [pwmReadingValue]
        #add gain, pwmReadingValue is the duty cycle in % eg.50% (pwmReadingValue = pwmReadingValue + someVolt * gain) 
        pwmReadingValue = str(pwmReadingValue)
        self.log("PWM reading: " + pwmReadingValue)
        return pwmReadingValue

    # Read lux sensor value on I2C pins
    def read_lux_sensor(self):
        # Get I2C bus
        bus = smbus.SMBus(1)
        # TSL2561 address, 0x39(57)
        # Select control register, 0x00(00) with command register, 0x80(128)
        #       0x03(03)    Power ON mode
        bus.write_byte_data(0x39, 0x00 | 0x80, 0x03)
        # TSL2561 address, 0x39(57)
        # Select timing register, 0x01(01) with command register, 0x80(128)
        #       0x02(02)    Nominal integration time = 402ms
        bus.write_byte_data(0x39, 0x01 | 0x80, 0x02)
        # Read data back from 0x0C(12) with command register, 0x80(128), 2 bytes
        # ch0 LSB, ch0 MSB
        data = bus.read_i2c_block_data(0x39, 0x0C | 0x80, 2)
        # Read data back from 0x0E(14) with command register, 0x80(128), 2 bytes
        # ch1 LSB, ch1 MSB
        data1 = bus.read_i2c_block_data(0x39, 0x0E | 0x80, 2)
        # Convert the data
        ch0 = data[1] * 256 + data[0]
        ch1 = data1[1] * 256 + data1[0]
        # Output data to screen
        # print "Full Spectrum(IR + Visible) :%d lux" %ch0
        # print "Infrared Value :%d lux" %ch1
        # print "Visible Value :%d lux" %(ch0 - ch1)
        return (ch0 - ch1)/2.

    # simple utility to print debug info, when in debug mode
    def log(self, s):
        if self.debug:
            print(s)        
    
#######################################################
#PWM_Reader: Class to read PWM and calculate duty cycle 
#######################################################

class PWM_Reader:
    # A class to read PWM pulses and calculate their frequency
    # and duty cycle.  The frequency is how often the pulse
    # happens per second.  The duty cycle is the percentage of
    # pulse high time per cycle.
    def __init__(self, pi, gpio, weighting=0.0):
        self.pi = pi
        self.gpio = gpio
        if weighting < 0.0:
                weighting = 0.0
        elif weighting > 0.99:
                weighting = 0.99
        self._new = 1.0 - weighting  # Weighting for new reading.
        self._old = weighting       # Weighting for old reading.
        self._high_tick = None
        self._period = None
        self._high = None
        pi.set_mode(gpio, pigpio.INPUT)
        self._cb = pi.callback(gpio, pigpio.EITHER_EDGE, self._cbf)

    def _cbf(self, gpio, level, tick):
        if level == 1:
            if self._high_tick:
                t = pigpio.tickDiff(self._high_tick, tick)
                if self._period:
                    self._period = (self._old * self._period) + (self._new * t)
                else:
                    self._period = t
            self._high_tick = tick
        elif level == 0:
            if self._high_tick:
                t = pigpio.tickDiff(self._high_tick, tick)
                if self._high:
                    self._high = (self._old * self._high) + (self._new * t)
                else:
                    self._high = t

    # Returns the PWM duty cycle percentage.
    def duty_cycle(self):
        if self._high:
                return 100.0 * self._high / self._period
        return 0.0

#######################################################
#MAIN
#######################################################

def exit_cleaner(signal, frame):
        print('You pressed Ctrl+C!, exiting...')
        GPIO.cleanup()  
        sys.exit(0)

#Input parameters:
#   "debug" for printing debugging info
#   "nolux" to not read data from lux
#   "pwm" to use PWM signals intead of digital

if __name__ == '__main__':
    debug = False
    nolux = False
    digital = True

    #parse input parameters
    for i in sys.argv:
        if i == "debug":
            debug = True
        elif i == "nolux":
            nolux = True
        elif i == "pwm":
            digital = False

    #setup cleaner on exit
    signal.signal(signal.SIGINT, exit_cleaner)

    client = Client(debug, nolux, digital)
    #start client
    client.start()
    #should not reach here
    assert False

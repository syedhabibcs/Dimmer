import requests
import os
import smbus
import time
import sys
import numpy as np

# Rasberry pi specific imports
import RPi.GPIO as GPIO
import pigpio

import signal

#Execute: "sudo pigpiod"
class Client:
    url = 'http://140.193.205.31:5000'
#     url = 'http://140.193.220.241:5000'
#     url = 'https://dimmerbrightness.herokuapp.com/'

    gpio_input = {}
    DEBUG = None
    pwmReader = None
    nolux = None
    digital = None
    pwmValues = None

    def __init__(self, debug, nolux, digital):
        self.DEBUG = debug
        self.nolux = nolux
        self.digital = digital
        self.pwmValues = []
        self.setUpGPIO()

        if not digital:
            self.pwmReader = Reader(pigpio.pi(), 5)
            print("reaches in const")


    def connect(self, url, isGet, lux_value):
        try:
            if isGet:
                response = requests.get(url)
            else:
                response = requests.post(url, lux_value)                        
        except requests.exceptions.ConnectionError:
            print("Error: Failed request trying again.")
            response = self.connect(url, isGet, lux_value)

        assert response.status_code == 200
        return response

    def showJsonFormattedData(self):
        response = self.connect(Client.url)
        data = response.json()
        self.log('Printing Json Formatted Data: ')
        self.log(data['1'])

    def showReceivedLEDSignal(self):
        response = self.connect(Client.url, True, None)
        data = response.text
        return data

    def sendLuxSensorValue(self):
        while True:
            if not self.nolux:
                    lux_value = '{:0.2f}'.format(
                        self.getLuxSensorValue())
            else:
                    lux_value = -1
            self.log("lux_sensor: " + str(lux_value))
            Client.gpio_input['lux_sensor_value'] = lux_value
            Client.gpio_input['power'] = self.receiveFromGPIO()
            response = self.connect(
                Client.url, False, Client.gpio_input)
            time.sleep(1)
            led_brightness = response.text
            self.log("Intensity: "+led_brightness)
            self.setToGPIO(led_brightness)

    def setUpGPIO(self):
        numOfBits = 4  # number of bits required to represent the required states
        numOfInputBits = 7
        # will set the GPIO pins
        gpio__out_pins = [17, 27, 22, 23]  # Using BCM modes
        if self.digital:
            gpio__in_pins=[6, 13, 19, 26, 16, 20, 21] #Using BCM modes
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        for i in range(0, numOfBits):
            GPIO.setup(gpio__out_pins[i], GPIO.OUT)
        if self.digital:
            for i in range(0, numOfInputBits):
                GPIO.setup(gpio__in_pins[i], GPIO.IN)

    def setToGPIO(self, led_brightness):
        numOfBits = 4  # number of bits required to represent the required states
        # will set the GPIO pins
        gpio__out_pins = [17, 27, 22, 23]  # Using BCM modes

        pinToSet = self.ledBrightnessToGpio(led_brightness)
        self.log("GPIO Pins: "+pinToSet)

        for i in range(0, numOfBits):
            if int(pinToSet[i]) == 1:
                    GPIO.output(gpio__out_pins[i], GPIO.HIGH)
            else:  # Redundent, left for future uses
                    GPIO.output(gpio__out_pins[i], GPIO.LOW)
            # time.sleep(1)

        return None

    def receiveFromGPIO(self):
        if self.digital:
            numOfBits = 7 #number of bits required to represent the required states
            # # will set the GPIO pins
            gpio__in_pins=[6, 13, 19, 26, 16, 20, 21] #Using BCM modes
            
            power_Binary=""

            for i in range(0,numOfBits):
                power_Binary+= str(GPIO.input(gpio__in_pins[i]))
        #     print(power_Binary)
            return str(int(power_Binary,2))

        else:
            pwmReadingValue = int(round(self.pwmReader.duty_cycle()))


            if( len(self.pwmValues) == 0):
                mean = 500
            else:
                mean = np.mean(self.pwmValues)

        #     print(abs(mean - pwmReadingValue))

            if abs(mean - pwmReadingValue) <= 2:
                # print("received" + str( pwmReadingValue ) + " old value" + str (self.pwmValues[-1]) )
                pwmReadingValue = self.pwmValues[-1]
                self.pwmValues.append(pwmReadingValue)
                if len(self.pwmValues) > 5:
                    self.pwmValues.pop(0)
            else:
                self.pwmValues = [pwmReadingValue]

            pwmReadingValue = str(pwmReadingValue)

            self.log("PWM reading: " + pwmReadingValue)

            return pwmReadingValue
        

    def getLuxSensorValue(self):
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

        return (ch0 - ch1)/2.;

    # Given the led brightness percentage as a string will convert it to the corresponding binary to set the GPIO pins

    def ledBrightnessToGpio(self, led_brightness):

        binary = "{0:b}".format(int(led_brightness)//10)
        if len(binary) != 4: binary = (4-len(binary))*'0'+binary
        return binary

    def log(self, s):
        if self.DEBUG:
            print(s)        
    





class Reader:
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

            if self._high_tick is not None:
                t = pigpio.tickDiff(self._high_tick, tick)

                if self._period is not None:
                    self._period = (self._old * self._period) + (self._new * t)
                else:
                    self._period = t

            self._high_tick = tick

        elif level == 0:

            if self._high_tick is not None:
                t = pigpio.tickDiff(self._high_tick, tick)

                if self._high is not None:
                    self._high = (self._old * self._high) + (self._new * t)
                else:
                    self._high = t

    # def frequency(self):
    #     """
    #     Returns the PWM frequency.
    #     """
    #     if self._period is not None:
    #         return 1000000.0 / self._period
    #     else:
    #         return 0.0

    # def pulse_width(self):
    #     """
    #     Returns the PWM pulse width in microseconds.
    #     """
    #     if self._high is not None:
    #         return self._high
    #     else:
    #         return 0.0

    def duty_cycle(self):
        # Returns the PWM duty cycle percentage.
        if self._high is not None:
                return 100.0 * self._high / self._period
        else:
                return 0.0

    # def cancel(self):
    #     """
    #     Cancels the reader and releases resources.
    #     """
    #     self._cb.cancel()

def signal_handler(signal, frame):
        print('You pressed Ctrl+C!, exiting...')
        GPIO.cleanup()  
        sys.exit(0)


if __name__ == '__main__':

    debug = False
    nolux = False
    digital = False

    for i in sys.argv:
        if i == "debug":
            debug = True
        elif i == "nolux":
            nolux = True
        elif i == "digital":
            digital = True

    signal.signal(signal.SIGINT, signal_handler)

    client = Client(debug, nolux, digital)
    client.sendLuxSensorValue()



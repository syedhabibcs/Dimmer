import requests
import os
import time

# Rasberry pi specific imports
# import RPi.GPIO as GPIO

class Client:

    url = 'http://0.0.0.0:5000/'
    signalUrl = 'http://0.0.0.0:5000/signal/'

    lux_sensor = {}

    def connect(self, url, isGet, lux_value):
        if isGet:
            response = requests.get(url)
        else:
            response = requests.post(url, lux_value)

        assert response.status_code == 200
        
        return response

    def showJsonFormattedData(self):
        response = self.connect(Client.url)
        data=response.json()
        print('Printing Json Formatted Data: ')
        print(data['1'])

    def showReceivedLEDSignal(self):
        response = self.connect(Client.url, True, None)
        data=response.text
        return data

    def sendLuxSensorValue(self):
        Client.lux_sensor['lux_sensor_value'] = '50'
        response = self.connect(Client.url, False, lux_sensor)


    def setGPIO(self, led_brightness):
        numOfBits = 4 #number of bits required to represent the required states
        # will set the GPIO pins
        gpio_pins=[4, 17, 27, 22] #Using BCM modes
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        for i in range(0,numOfBits4):
            GPIO.setup(pin[i], GPIO.OUT)

        pinToSet = self.ledBrightnessToGpio()

        for i in range(0,numOfBits4):
            if int(pinToSet[i]) == 1:
                GPIO.output(gpio_pins[i], GPIO.HIGH)
            else:   #Redundent, left for future uses
                GPIO.output(gpio_pins[i], GPIO.LOW)
            time.sleep(1)


        return None

    #Given the led brightness percentage as a string will convert it to the corresponding binary to set the GPIO pins
    def ledBrightnessToGpio(self, led_brightness):

        binary = "{0:b}".format(int(led_brightness)//10)
        if len(binary)!=4: binary = (4-len(binary))*'0'+binary
        return binary

if __name__ == '__main__':
    l=[8,2,3,4,5]
    lux_sensor={'lux_sensor_value':'50'}
    
   
    client = Client()
    signal = client.showReceivedLEDSignal()

    print('Printing Signal Received From the Server: %s'%signal)

    client.sendLuxSensorValue()

    # binary = client.ledBrightnessToGpio(signal)
    # print(binary)
    # #sending the lux sensor value through the post request
    # response = requests.post('http://0.0.0.0:5000/', lux_sensor)
    # assert response.status_code == 200
    # print(response.text)

    

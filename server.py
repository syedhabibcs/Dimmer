from flask import Flask, render_template, request
import json
import requests
from datetime import datetime
import threading
import time

class Server:

    # This will be set from the user input from the web client
    lux_svalue = 0
    led_brightness = 50

    chart_seconds = []

    def run(self):
        app = Flask(__name__)
        
        return app

    def routes(self):

        @app.route('/',methods = ["GET","POST"])
        def index():
            if request.method == "POST":
                # printing the lux sensor value received from the post request
                Server.lux_svalue = request.form['lux_sensor_value']
                print(request)
                print("Printing the lux sensor value received from Client: %s"%Server.lux_svalue)
            return str(Server.led_brightness)
            

        @app.route("/signal/",methods = ["GET","POST"])
        def setSignal():
            if request.method == "POST":
                for field in request.form.keys():
                    value = request.form[field]
                    self.setLedBrightness(value)
                    print(value)
            return render_template("main.html")

        @app.route("/flux/",methods = ["GET","POST"])
        def getFluxValue():
            return json.dumps({'lux_value': str(Server.lux_svalue)})

        @app.route("/chart/",methods = ["GET","POST"])
        def getChartValue():
            # Server.chart_seconds.append((1,2))
            # Server.chart_seconds.append((3,4))

            chart_dic = {'seconds': Server.chart_seconds}
            return json.dumps(chart_dic)

    def createChartValueSeconds(self):
        for i in range(0,12):
            # Server.chart_seconds.append((datetime.now().strftime('%H:%M:%S'), Server.lux_svalue))
            Server.chart_seconds.append((int(time.time()), Server.lux_svalue))
            time.sleep(5)
        while True:
            Server.chart_seconds.pop(0)
            Server.chart_seconds.append((int(time.time()), Server.lux_svalue))
            time.sleep(5)


    def setLedBrightness(self, led_brightness):
            Server.led_brightness = led_brightness

if __name__ == '__main__':
    server = Server()
    app =  server.run()
    server.routes()
    thread = threading.Thread(target=server.createChartValueSeconds, args=())
    thread.daemon = True                            # Daemonize thread
    thread.start()
    app.run(debug=True, host='0.0.0.0')




#Extra reference code

# return json.dumps({'1':'Hello world'})

# This route returns the html page instead of returning the json value
        # @app.route('/',methods = ["GET","POST"])
        # def index():
        #     print(request)
        #     return render_template("main.html")
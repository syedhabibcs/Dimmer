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

    led_brightness_controller = False #false means manual meaning controlled by slider and True means scheduling

    action=[]


    def run(self):
        app = Flask(__name__)
        
        return app

    def routes(self):

        @app.route('/',methods = ["GET","POST"])
        def index():
            if request.method == "POST":
                # printing the lux sensor value received from the post request
                Server.lux_svalue = request.form['lux_sensor_value']
                # print("Printing the lux sensor value received from Client: %s"%Server.lux_svalue)
            return str(Server.led_brightness)
            

        @app.route("/signal/",methods = ["GET","POST"])
        def setSignal():
            if request.method == "POST":
                for field in request.form.keys():
                    value = request.form[field]
                    if (Server.led_brightness_controller)==False:
                        self.setLedBrightness(value)
                        print(value)
            return render_template("main.html")

        @app.route("/flux/",methods = ["GET","POST"])
        def getFluxValue():
            return json.dumps({'lux_value': str(Server.lux_svalue)})

        @app.route("/action/",methods = ["GET","POST"])
        def registerAction():
            if request.method == "POST":
                
                time = request.form['time']
                unixTime = self.stringtoUnixTime(time)
                intensity = str(int(request.form['intensity'])*10)
                radio = request.form['radio']
                
                #
                Server.led_brightness_controller = radio
                if Server.led_brightness_controller:
                    Server.action.append((str(unixTime),intensity))
                    print(time)
                    print(str(unixTime))
                    Server.action = sorted(Server.action, key=lambda tup: (tup[0]))
                    print(Server.action)
            return "Test"

        @app.route("/schedules/",methods = ["GET","POST"])
        def getSchedules():
            return json.dumps(dict(Server.action))
            # return Server.action



        @app.route("/chart/",methods = ["GET","POST"])
        def getChartValue():
            time_lux = ((int(time.time()), Server.lux_svalue))
            chart_dic={'seconds': time_lux}
            return json.dumps(chart_dic)
            

    def stringtoUnixTime(self, string_time):
        addedYMD = time.strftime("%Y")+"-"+time.strftime("%m")+"-"+time.strftime("%d")+" "+string_time
        dt = datetime.strptime(addedYMD, "%Y-%m-%d %H:%M:%S")
        unixTime = time.mktime(dt.timetuple())
        return str(int(unixTime))


    def setLedBrightness(self, led_brightness):
            Server.led_brightness = led_brightness

    def sendScheduledSignals(self):
        
        timeToCompare = ""
        while True:
            if Server.led_brightness_controller:
                print("Server time to send: "+str(Server.led_brightness))
                string_time = str(int(time.time()))
                if len(Server.action)>0:
                    timeToCompare = Server.action[0]
                    print("Action Time:"+timeToCompare[0] +"    |    System Time:"+string_time+"    |  Server Time To Send: "+str(Server.led_brightness))
                    if string_time == timeToCompare[0]:
                        Server.led_brightness = timeToCompare[1]
                        Server.action.pop(0)
                time.sleep(1)

if __name__ == '__main__':
    server = Server()
    app =  server.run()
    server.routes()
    thread = threading.Thread(target=server.sendScheduledSignals, args=())
    thread.daemon = True                            # Daemonize thread
    thread.start()
    app.run(debug=True, host='0.0.0.0')



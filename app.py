from flask import Flask, render_template, request
import json
import requests
from datetime import datetime
import threading
import time

app = Flask(__name__)

class Server:

    # This will be set from the user input from the web client
    lux_svalue = 0
    led_brightness = 50

    power = 0

    led_brightness_controller = False #false means manual meaning controlled by slider and True means scheduling

    isActionValid = True
    action=[]

    @app.route('/',methods = ["GET","POST"])
    def index():
        if request.method == "POST":
            Server.lux_svalue = request.form['lux_sensor_value']
            Server.power = request.form['power']
            # print("Printing the lux sensor value received from Client: %s"%Server.lux_svalue)
        return str(Server.led_brightness)
            

    @app.route("/signal/",methods = ["GET","POST"])
    def setSignal():
        if request.method == "POST":
            for field in request.form.keys():
                value = request.form[field]
                Server.led_brightness_controller=False
                Server.led_brightness = value                     
        return render_template("main.html")

    @app.route("/flux/",methods = ["GET","POST"])
    def getFluxValue():
        return json.dumps({'lux_value': str(Server.lux_svalue)})

    @app.route("/action/",methods = ["GET","POST"])
    def registerAction():
        if request.method == "POST":
            
            user_time = request.form['time']

            addedYMD = time.strftime("%Y")+"-"+time.strftime("%m")+"-"+time.strftime("%d")+" "+user_time
            dt = datetime.strptime(addedYMD, "%Y-%m-%d %H:%M:%S")
            unixTime = str(int(time.mktime(dt.timetuple())))

            intensity = str(int(request.form['intensity'])*10)
            radio = request.form['radio']
            
            #
            if radio == 'true':
                Server.led_brightness_controller = True

            
            if Server.led_brightness_controller:
                
                if str(time.time())<=unixTime:
                    
                    action_temp = dict(Server.action)
                    action_temp[unixTime] = intensity
                    Server.action = [(k,v) for (k,v) in action_temp.items()]

                    Server.isActionValid = True
                    
                    Server.action = sorted(Server.action, key=lambda tup: (tup[0]))
                    
                else:
                    Server.isActionValid = False
        return json.dumps(dict(Server.action))

    @app.route("/schedules/",methods = ["GET","POST"])
    def getSchedules():
        action_dict = dict(Server.action)
        action_dict['valid']= Server.isActionValid
        return json.dumps(action_dict)

    @app.route("/chart/",methods = ["GET","POST"])
    def getChartValue():
        time_lux = ((int(time.time()), Server.lux_svalue))
        chart_dic={'seconds': time_lux, 'led_brightness': Server.led_brightness,'power': Server.power}
        return json.dumps(chart_dic)

    def sendScheduledSignals(self):
        
        timeToCompare = ""
        while True:
            print("Inside")
            if Server.led_brightness_controller:
                string_time = str(int(time.time()))
                if len(Server.action)>0:
                    timeToCompare = Server.action[0]
                    if string_time >= timeToCompare[0]:
                        
                        Server.led_brightness = timeToCompare[1]
                        Server.action.pop(0)
                     
                time.sleep(1)

if __name__ == '__main__':
    server = Server()
    thread = threading.Thread(target=server.sendScheduledSignals, args=())
    thread.daemon = True                            # Daemonize thread
    thread.start()
    app.run(debug=True, host='0.0.0.0')



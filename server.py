from flask import Flask, render_template, request
import json
import requests
from datetime import datetime
import threading
import time

app = Flask(__name__)

class Server:

    # This will be set from the user input from the web client
    action=[]
    power = 0
    lux_svalue = 0
    led_brightness = 100
    isActionValid = True
    led_brightness_controller = False #false-manual meaning controlled by slider || True means scheduling

    @app.route('/',methods = ["GET","POST"])
    def index():
        if request.method == "POST":
            Server.lux_svalue = request.form['lux_sensor_value']
            Server.power = request.form['power']
        return str('Website is hosted at: http://dimmerbrightness.herokuapp.com/signal/')
            

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
            radio = request.form['radio']
            if radio == 'true':
                Server.led_brightness_controller = True

            user_time = request.form['time']
            addedYMD = time.strftime("%Y")+"-"+time.strftime("%m")+"-"+time.strftime("%d")+" "+user_time
            dt = datetime.strptime(addedYMD, "%Y-%m-%d %H:%M:%S")
            unixTime = str(int(time.mktime(dt.timetuple())))
            intensity = str(int(request.form['intensity'])*10)
            
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
        if Server.led_brightness_controller:
            if len(Server.action)>0:
                timeToCompare = Server.action[0]
                string_time = str(int(time.time()))
                if string_time >= timeToCompare[0]:
                    Server.led_brightness = timeToCompare[1]
                    Server.action.pop(0)
        time_lux = ((int(time.time()), Server.lux_svalue))
        chart_dic={'seconds': time_lux, 'led_brightness': Server.led_brightness,'power': Server.power}
        return json.dumps(chart_dic)

if __name__ == '__main__':
    server = Server()
    app.run(debug=True, host='0.0.0.0')
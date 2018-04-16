from flask import Flask, render_template, request
import json
import requests


class Server:

    # This will be set from the user input from the web client
    lux_svalue = 0
    led_brightness = 5

    def run(self):
        app = Flask(__name__)
        
        return app

    def routes(self):

        @app.route('/',methods = ["GET","POST"])
        def index():
            if request.method == "POST":
                # printing the lux sensor value received from the post request
                lux_svalue = request.form['lux_sensor_value']
                print("Printing the lux sensor value received from Client: %s"%lux_svalue)
            return str(Server.led_brightness)
            

        @app.route("/signal/")
        def sendSignal():
            return render_template("main.html")


if __name__ == '__main__':
    server = Server()
    app =  server.run()
    server.routes()
    app.run(debug=True, host='0.0.0.0')




#Extra reference code

# return json.dumps({'1':'Hello world'})

# This route returns the html page instead of returning the json value
        # @app.route('/',methods = ["GET","POST"])
        # def index():
        #     print(request)
        #     return render_template("main.html")
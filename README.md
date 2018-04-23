# Dimmer

Hosted at: https://dimmerbrightness.herokuapp.com/signal/

## Running the Client Script
There are 2 configurations for client script. This instructions assume the file is on desktop.
To run script: Open terminal, execute "cd Desktop", now we should be in Desktop where the client script resides.

### Different Configurations:
1. "python client.py": this runs client with lux sensor with no output on terminal
2. "python client.py nolux": this runs client without lux sensor (-1) with no output on terminal
3. "python client.py debug": this runs client with lux sensor and prints output. This could be used to see client is sending and getting sensible data from server.
4. "python client.py debug nolux": this runs client without lux sensor and prints output. This could be used to see client is sending and getting sensible data from server.

### Troubleshooting for client:
If client is not working even after re-running script, use debug (configuration 3 or 4) and if there is only 1 ouput line and nothing more, it means client cannot connect to server. Possibly because server is down or PI isn't connected to net.

## Setup Raspberry PI from start to running client script:
1. Install raspbian
2. Connect to internet and update the system (sudo apt-get update)
3. Enable SSH , VNC and I2C in "Raspberry Pi Configuration"/Interfaces.
    - SSH: for file transfer
    - VNC: to manage client script
    - I2C: for lux sensor
4. Reboot and setup VNC server
    - Create an account and sign in PI
    - Choose Direct and cloud connectivity: this lets you automatically access PI after start up
5. Copy the client.py file from GitHub to Desktop (using some FTP like filezilla or SSH)
6. Run the client script

## Connecting to UofM (EAP) internet
You will need to access PI somehow for the first time, probably using a monitor.
1. In terminal type: "sudo nano /etc/wpa_supplicant/wpa_supplicant.conf"
2. A file would open up, go at the bottom and type:
`network={
  ssid="uofm-secure"
  key_mgmt=WPA-EAP
  eap=PEAP
  identity="your@myumanitoba.ca"
  password="yourPassword"
  phase2="auth=MSCHAPv2"
}`
3. Press Ctrl+X, y, enter to save the file.

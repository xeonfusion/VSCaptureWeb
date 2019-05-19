# VSCaptureWeb
VSCaptureWeb (C) 2019 John Pateman johnpateman@me.com, John George K. xeonfusion@yahoo.com,

Web interface for VSCapture, software to capture and validate physiological data acquired from a variety of anaesthetic equipment.

Presents a web interface on localhost:9090 to allow the remote configuration of the logging parameters and to facilitate starting and stopping the logging process remotely.

Tested on RaspberryPi 3B+ (Raspbian OS), Python3, to run as a server in a headless setup. Can be added to autostart script on reboot in RPi.

## SETUP

1)Install Python3, and Mono runtime environment in RaspberryPi:
```
apt-get install python3
apt-get install mono-complete
```

2)Install requirements.txt with PIP3:
```
pip3 install -r requirements.txt
```
3) Make sure latest version of PySimpleGUIWeb is installed:
```
pip3 install --upgrade pysimpleguiweb
```
4) Use updated version of VSCapture binary attached with VSCaptureWeb.

## RUN

From command line (or add command to autostart at reboot):
```
python3 vscaptureweb.py
```
To run as a background process:
```
python3 vscaptureweb.py&
```

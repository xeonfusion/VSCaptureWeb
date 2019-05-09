'''
VSCaptureWeb (C) 2019 John Pateman johnpateman@me.com, John George K. xeonfusion@yahoo.com,
Web interface to VSCapture, software to capture and validate physiological data acquired
from a variety of anaesthetic equipment.
Presents a web interface on localhost:9090 to allow the configuration of the logging parameters and
to facilitate starting and stopping the logging process
'''

import asyncio
import os
import shlex
import subprocess
from subprocess import PIPE, STDOUT, Popen
import PySimpleGUIWeb as sg
import serial.tools.list_ports

#monoPath = '/Library/Frameworks/Mono.framework/Versions/Current/Commands/mono'
monoPath = '/usr/bin/mono-sgen'

WEBPORT = 9090

INTERVALS = {
    "5 Sec": "5",
    "10 Sec": "10",
    "30 Sec": "30",
    "1 Min": "60",
    "3 Mins": "180",
    "5 Mins": "300"
}

WAVESETS = {
    "None": "0",
    "ECG1, INVP1, INVP2, PLETH": "1",
    "ECG1, INVP1, PLETH, CO2, RESP": "2",
    "ECG1, PLETH, CO2, RESP, AWP, VOL, FLOW": "3",
    "ECG1, ECG2": "4",
    "EEG1, EEG2, EEG3, EEG4": "5"
}

EXPORTOPTIONS = {
    "CSV files" : "1",
    "CSV files and JSON URL" : "2"
}

LOGGING = False

OUTPUT = ''

OUTSTRLIST = list()

def readConfig():
    '''
    Read baseline configuration from a vscapture.conf file
    '_" delimited file containing the saved default values for
    port, logging interval & set of waves to record
    '''
    try:
        fh = open('vscapture.conf', 'r')
        config = fh.read()
        port, freq, sets, export = config.split("_")
        if port == 'None':
            port = "/dev/ttyUSB0"
        interval = next(
            key for key, value in INTERVALS.items() if value == freq)
        wave = next(key for key, value in WAVESETS.items() if value == sets)
        exportoption = next(key for key, value in EXPORTOPTIONS.items() if value == export)
#        return (port, interval, wave)
    except FileNotFoundError:
        port = "/dev/ttyUSB0"
        interval = "10 Sec"
        wave = "None"
        exportoption = "CSV files"
    return (port, interval, wave, exportoption)


def writeConfig(config):
    '''
    Write out current configuration to the vscapture.conf file
    Format is port_interval_waveset
    '''
    try:
        fh = open('vscapture.conf', 'w')
        fh.write(config)
        fh.close()
        return
    except FileNotFoundError:
        print('Error - preferences not saved')


def getAvailable():
    '''
    Get a list of available ports
    '''
    available = []
    comPortList = serial.tools.list_ports.comports()
    for portname in comPortList:
        available.append(portname.device)
    return available


async def read_stream(stream, callback):
    while True:
        if not LOGGING:
            break
        #        global LOGGING
        if LOGGING:
            line = await stream.readline()
            if line:
                callback(line)
            else:
                break


async def stream_subprocess(cmd, stdout_cb, stderr_cb):
    process = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)

    await asyncio.wait(
        [
            read_stream(process.stdout, stdout_cb),
            read_stream(process.stderr, stderr_cb)
        ],
        return_when=asyncio.FIRST_COMPLETED)
    #    global LOGGING
    if not LOGGING:
        return await process.terminate()
    else:
        return await process.wait()


def readstdoutstr(line):
    line.strip()
    OUTPUT = line.decode('utf-8')
    OUTSTRLIST.append(OUTPUT)
    outputstrs = '\n'.join(OUTSTRLIST)
    window.Element('_MULTIOUT_').Update((outputstrs), append=False)
    #window.Element('_MULTIOUT_').Update((OUTPUT), append=False)
    #print(OUTPUT)
    if(len(OUTSTRLIST) >10):
        OUTSTRLIST.clear()
    window.Refresh()
    check_stop_loop()


async def readsubprocess(args):
    process = await stream_subprocess(args, lambda x: readstdoutstr(x),
                                      lambda x: print("STDERR: %s" % x))
    #    global LOGGING
    if not LOGGING:
        # process.communicate(ESCAPE_KEY)
        process.stdout.close()
        process.terminate()
        LOGGING = False


def check_stop_loop():
    event, __ = window.Read(timeout=10)
    if event in (None, 'Stop Logging'):
        global LOGGING
        LOGGING = False
        window.Element('_MULTIOUT_').Update(("Stopping logging"), append=True)
        #print("Stopping logging")
        window.Refresh()



port, interval, wave, exportoption = readConfig()
connected = getAvailable()

# The GUI layout
layout = [[
    sg.Text('VSCapture Web Interface', size=(120, 4), font=('Helvetica', 24))
], [
    sg.Combo(
        values=connected,
        default_value=port,
        key='_PORT_',
        enable_events=True,
        readonly=False,
        tooltip='Select port that is connected to the anaesthetic machine',
        disabled=False,
        size=(30, 1)),
    sg.Text('Port', size=(60, 1), font=('Helvetica', 16))
], [
    sg.Combo(
        values=list(INTERVALS.keys()),
        default_value=interval,
        key='_INTERVAL_',
        enable_events=True,
        readonly=False,
        tooltip='How frequently do you want to log the data?',
        disabled=False,
        size=(30, 1)),
    sg.Text('Logging interval', size=(60, 1), font=('Helvetica', 16))
], [
    sg.Combo(
        values=list(WAVESETS.keys()),
        default_value=wave,
        key='_WAVE_',
        enable_events=True,
        readonly=False,
        tooltip='Which waveset',
        disabled=False,
        size=(30, 1)),
    sg.Text('Wave set', size=(60, 1), font=('Helvetica', 16))
], [
    sg.Combo(
        values=list(EXPORTOPTIONS.keys()),
        default_value=exportoption,
        key='_EXPORTOPTION_',
        enable_events=True,
        readonly=False,
        tooltip='Choose data export format option',
        disabled=False,
        size=(30, 1)),
    sg.Text('Data export option', size=(60, 1), font=('Helvetica', 16))
], [
    sg.InputText(
        default_text='',
        key='_DEVIDINPUT_',
        enable_events=False,
        tooltip='Input Device ID/Name for JSON export',
        disabled=False,
        size=(30,1),
        do_not_clear=True,
        ),
        sg.Text('Device ID/Name', size=(30,1), font=('Helvetica, 16'))
],  [
    sg.InputText(
        default_text='',
        key='_JSONURLINPUT_',
        enable_events=False,
        tooltip='Input JSON Data Export URL(http://)',
        disabled=False,
        size=(60,1),
        do_not_clear=True,
        ),
        sg.Text('JSON data export URL(http://)', size=(30,1), font=('Helvetica, 16'))
], [
    sg.Button('Start Logging', button_color=('white', 'blue')),
    sg.Button('Stop Logging', button_color=('white', 'green')),
    sg.Button('Stop Server', button_color=('white', 'red'))
], [
    sg.Multiline(
        'Data Output',
        size=(160, 12),
        key='_MULTIOUT_',
        font='Courier 14',
        autoscroll=True,)
    
]]
'''
sg.Output(size=(160,12))
    '''

# create the "Window"
window = sg.Window(
    'VSCapture Logging Interface', layout=layout,
    default_element_size=(60, 2),
    font='Helvetica 18',
    web_port=WEBPORT, web_start_browser=False,
    web_multiple_instance=True, disable_close=True, 
)

print("Started VSCaptureWeb(C) 2019 VSCapture web interface server on localhost:" + str(WEBPORT))

#  The "Event loop" where all events are read and processed (button clicks, etc)
while True:
    event, values = window.Read(timeout=100)
    #getAvailable()
    #event, values = window.Read(timeout=0)
    # read with a timeout of 100 ms

    if event != sg.TIMEOUT_KEY:  # if got a real event, print the info
        port = values['_PORT_']
        freq = values['_INTERVAL_']
        interval = INTERVALS.get(freq)
        sets = values['_WAVE_']
        wave = WAVESETS.get(sets)
        export = values['_EXPORTOPTION_']
        exportoption = EXPORTOPTIONS.get(export)
        devid = values['_DEVIDINPUT_']
        jsonurl = values['_JSONURLINPUT_']
        config = str(port) + "_" + str(interval) + "_" + str(wave) + "_" + str(exportoption)

        # writeConfig(config)

    # if the "Exit" button is clicked or window is closed then exit the event loop
    if event in (None, 'Stop Server'):
        break

    if event in (None, 'Start Logging'):
        if not LOGGING:
            LOGGING = True
            window.Element('_MULTIOUT_').Update(
                ("Starting logging"), append=True)
            #print("Starting logging")  
            full_path = os.path.realpath(__file__)
            path, filename = os.path.split(full_path)
            filepath = path + "/VSCapture.exe"
            args = monoPath + " " + filepath + " -port " + \
                str(port) + " -interval " + \
                str(interval) + " -waveset " + \
                str(wave) + " -export " + str(exportoption) 
            if str(exportoption) == "2":        
                args += " -devid " + str(devid) + " -url " + str(jsonurl)
            
            window.Element('_MULTIOUT_').Update((args), append=True)
            #print(args)
            window.Element('_MULTIOUT_').Update((OUTPUT), append=True)
            #print(OUTPUT)
            args = shlex.split(args)

            loop = asyncio.get_event_loop()
            try:
                loop.run_until_complete(readsubprocess(args))
            except:
                print("Exiting process loop")
            finally:
                # loop.close()
                LOGGING = False

    if event in (None, 'Stop Logging'):
        window.Element('_MULTIOUT_').Update(("Stopping logging"), append=True)
        window.Refresh()
        LOGGING = False

# Handle start/stop logging here
window.Element('_MULTIOUT_').Update(("Stopping Server, Bye"), append=True)
#print("Logging out, Bye")
window.Close()
config = str(port) + "_" + str(interval) + "_" + str(wave) + "_" + str(exportoption)
writeConfig(config)
print('Completed Shutdown')

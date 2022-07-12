import time 
import urllib2
import smbus2
import bme280
import argparse
import math
import sys
import requests

port = 1
address = 0x77
bus = smbus2.SMBus(port)

bme280.load_calibration_params(bus, address)

## Calculate dew point
def calculate(air_temp_c, rh, on_error = float('nan')):
    try:
        s1 = math.log(float(rh) / 100.0)
        s2 = (float(air_temp_c) * 17.625) / (float(air_temp_c) + 243.04)
        s3= s1 + s2
        s4 = (17.625 - s1) -s2
        dewpoint = 243.04 * s3 /s4
    except:
        dewpoint = on_error
    return dewpoint

def queryRepeatedly():
    while True:
        try:
            data = bme280.sample(bus, address)
            tempc = data.temperature
            tempf = (tempc * 1.8) + 32-1
            humidity = data.humidity
            pressure = data.pressure
            dewpointc = calculate(tempc, humidity)
            dewpointf = (dewpointc * 1.8) + 32
            psea = pressure / pow(1.0 - 61/44330.0, 5.255)
            pressurein = (psea * 0.0295301)

            ## Send to local influxDB
            url = 'http://localhost:8086/write?db=weather&u=admin&p=#redacted#'
            data = 'temphumidity,sensor=outside temp=%s,humidity=%s,pressure=%s,dewpoint=%s' % (tempf, humidity, pressurein, dewpointf)
            r = requests.post(url, data=data)

            ## Send to wunderground
            url = "https://weatherstation.wunderground.com/weatherstation/updateweatherstation.php?ID=#redacted#PASSWORD=#redacted#:now&tempf=%s&humidity=%s&baromin=%s&dewptf=%s&action=updateraw" % (tempf, humidity, pressurein, dewpointf)
            urllib2.urlopen(url).read()
        except:
            continue
        time.sleep(30)

queryRepeatedly()

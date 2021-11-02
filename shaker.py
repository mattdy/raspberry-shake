##!/usr/bin/python

# shaker.py
# Created by Matt Dyson (mattdyson.org)
# v1.0 - 12/01/16

# Shaker class designed to talk to a LIS3DH sensor to determine the amount of movement occuring
# Allows defining thresholds and periods for activation, and setting callback functions for when the sensor
#  is determined to have gone 'hot' or 'cold'

# Requirements:
#  Adafruit_I2C    - https://github.com/adafruit/Adafruit-Raspberry-Pi-Python-Code/tree/master/Adafruit_I2C
#  python-lis3dh   - https://github.com/mattdy/python-lis3dh
#  yunomi          - https://pypi.python.org/pypi/yunomi
#  LedControl      - http://projects.mattdyson.org/projects/LEDControl/

import threading
import time
from Adafruit_I2C import Adafruit_I2C
from LIS3DH import LIS3DH
from yunomi import Meter
from LedControl import LedControl

# Thread that monitors a LIS3DH sensor for any movement (one axis experiencing force greater than [1G + given sensitivity]), marking a Meter object each time it does
class VibrationLooper(threading.Thread):
   def __init__(self, meter, sensitivity):
      threading.Thread.__init__(self)
      self.daemon = True
      self.meter = meter
      self.sensor = LIS3DH(bus=1)
      self.sensitivity = 1 + sensitivity

      self.stopping = False

   def run(self):
      while not self.stopping:
         x = self.sensor.getX()
         y = self.sensor.getY()
         z = self.sensor.getZ()

         if any(True for val in [x,y,z] if val>self.sensitivity or val<-(self.sensitivity)):
            self.meter.mark()
            time.sleep(0.1)

   def stop(self):
      self.stopping = True

# Talks to a Meter object to determine the sensor state, given the specificied $sensitivity
# When the average activations exceeds $threshold for $warmup seconds, $hot_callback() will be called
# Subsequently, then the average activations goes below $threshold for $cooldown seconds, $cold_callback() will be called
# Pins at $hot_led and $cold_led will be lit and flashed appropriately
class Shaker:
   def __init__(self,
      hot_callback,
      cold_callback,
      threshold = 1,
      sensitivity = 0.1,
      warmup = 120,
      cooldown = 120,
      hot_led=26,
      cold_led=13,
      debug=False):
      
      self.debug = debug

      if self.debug:
         print "Parameters:"
         print "  threshold:     %s" % (threshold)
         print "  sensitivity:   %s" % (sensitivity)
         print "  warmup:        %s" % (warmup)
         print "  cooldown:      %s" % (cooldown)
         print "  hot_led:       %s" % (hot_led)
         print "  cold_led:      %s" % (cold_led)

      self.green = LedControl(hot_led)
      self.red = LedControl(cold_led)

      self.sensitivity = sensitivity

      self.meter = Meter()
      self.vibration = VibrationLooper(self.meter, self.sensitivity)
      self.vibration.start()

      self.stopping = False

      self.activated = False
      self.countUp = 0
      self.countDown = 0

      # Functions to call when we go hot/cold
      self.hotCallback = hot_callback
      self.coldCallback = cold_callback

      # Number of seconds we need to be above the threshold to say we're hot
      self.warmup = warmup

      # Number of seconds we need to be below the threshold to say we're cold
      self.cooldown = cooldown

      # Threshold at which we consider the sensor active
      self.threshold = 1

      while not self.stopping:
         rate = self.meter.get_one_minute_rate()
         if self.debug:
            print "Rate: %.4f   Activated: %r   CountUp: %s   CountDown: %s" % (rate, self.activated, self.countUp, self.countDown)
         
         if rate > self.threshold:
            # Rate above threshold
            if not self.activated:
               self.countDown = 0
               if self.countUp<self.warmup:
                  self.countUp+=1
                  self.red.setValue(100 * (self.countUp % 2)) # Flash red while we're warming up
               else:
                  self.activated = True
                  if self.debug:
                     print "Sensor has exceeded threshold for warmup - triggering 'hot' callback"
                  self.hotCallback()
            else:
               # Above threshold and active, so we should only have a green light
               self.countUp = 0
               self.countDown = 0
               self.green.setValue(100)
               self.red.setValue(0)

         else:
            # Rate below threshold
            if self.activated:
               self.countUp = 0
               if self.countDown<self.cooldown:
                  self.countDown+=1
                  self.green.setValue(100 * (self.countDown % 2)) # Flash green while we're cooling down
               else:
                  self.activated = False
                  if self.debug:
                     print "Sensor has gone below threshold for cooldown - triggering 'cold' callback"
                  self.coldCallback()
            else:
               # Below threshold and not active, so we should have only a red light
               self.countUp = 0
               self.countDown = 0
               self.red.setValue(100)
               self.green.setValue(0)

         time.sleep(1)

   def stop(self):
      self.stopping = True

   def __del__(self):
      self.vibration.stop()
      self.stopping = True

if __name__ == "__main__":
   def hot():
      print "Going hot"

   def cold():
      print "Going cold"

   try:
      shake = Shaker(hot, cold, warmup = 10, cooldown=10, debug=True)
   except (KeyboardInterrupt, SystemExit):
      print "Shutting down"

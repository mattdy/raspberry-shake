#!/usr/bin/python

import argparse
import requests
from shaker import Shaker

parser = argparse.ArgumentParser(description="Monitor for activation of a sensor, and send alerts")
parser.add_argument('--name', required=True, help="Name of the appliance we're monitoring")
parser.add_argument('--threshold', type=int, default=1, help="Threshold at which we consider the sensor active")
parser.add_argument('--sensitivity', type=float, default=0.1, help="Sensitivity of the sensor (movement threshold = 1+val)")
parser.add_argument('--warmup', type=int, default=120, help="Time for which a sensor must be active before triggering into a 'hot' state")
parser.add_argument('--cooldown', type=int, default=360, help="Time for which a sensor must be inactive before triggering into a 'cold' state")
parser.add_argument('--debug', dest='debug', action='store_true', help="Show debug information")
parser.set_defaults(debug=False)

args = parser.parse_args()

def activated():
   print "%s has started running" % (args.name)

def deactivated():
   print "%s has finished running" % (args.name)
   notify("%s has finished running" % (args.name), 10)

def notify(message, priority):
   path = 'http://einstein/notification?fromApplication=Appliance&priority=%s&message=%s' % (priority,message)
   r = requests.get(path)

   if r.status_code != 200:
      print "Error making request to %s - server returned %s" % (path, r.status_code)


print "Starting up appliance: %s" % (args.name)
try:
   shake = Shaker(activated, deactivated, threshold=args.threshold, sensitivity=args.sensitivity, warmup=args.warmup, cooldown=args.cooldown, debug=args.debug)
except (KeyboardInterrupt, SystemExit):
   print "Shutting down appliance"

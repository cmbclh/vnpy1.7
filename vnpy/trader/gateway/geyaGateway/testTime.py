import sys
import datetime
import time

print datetime.datetime.now()
#print time.localtime(datetime.datetime.now())
#print time.strftime('%Y%m%d%H%M%S%f',datetime.datetime.now())
print datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')

SYMBOL_BTCCNY = 'BTCCNY'
SYMBOL_ZECCNY = 'ZECCNY'
SYMBOL_MAP = {}
SYMBOL_MAP['btc_cny'] = SYMBOL_BTCCNY
SYMBOL_MAP['zec_cny'] = SYMBOL_ZECCNY
print SYMBOL_MAP
SYMBOL_MAP_REVERSE = {v: k for k, v in SYMBOL_MAP.items()}
print SYMBOL_MAP_REVERSE

reqDate = datetime.datetime.now().strftime('%Y%m%d')
reqTime = datetime.datetime.now().strftime('%H:%M:%S')
print reqDate
print reqTime
#!/usr/bin/python

import time

def open_log(logfile):
	log = open(logfile, 'a')
	date = time.strftime("%H:%M:%S")
	dash = ""
	for i in range(0, 79):
		dash += "-"
	write_log(log, dash)
	write_log(log, "Logfile " + logfile + " opened at " + date)
	write_log(log, dash)
	return log

def write_log(logfd, string):
	print >> logfd, string
	logfd.flush()

#!/usr/bin/python

import time
import os
import sys
sys.path.append("/usr/local/openvswitch/pylib/system")
import shell

def open_log(logfile):
	dir = os.path.dirname(logfile)
	cmd = 'mkdir -p ' + dir
	shell.call_prog_as_is(cmd)
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

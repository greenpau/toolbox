#!/usr/bin/python

import subprocess
import os
import sys
sys.path.append("/usr/local/aos/pylib/system")

def call_prog_as_is(cmd):
	p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
			     stderr=subprocess.STDOUT)
	outline = ""
	for line in p.stdout.readlines():
		if (line == "\n"):
			break
		outline = outline + line
		retval = p.wait()
	return outline

def whoami():
	return call_prog_as_is('whoami').replace("\n", "")

def getent(host):
	outstr = call_prog_as_is('getent hosts ' + host).replace("\n", "")
	return outstr.split(" ")[0]

def is_alive(host):
	cmd = "ping -c 1 " + host
	outstr = call_prog_as_is(cmd)
	if (outstr.find("64 bytes from") == -1):
		return False
	else:
		return True

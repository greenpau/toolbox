#!/usr/bin/python

import sys

sys.path.append("/usr/local/aos/pylib/system")
import shell

def getent(host):
	outstr = shell.call_prog_as_is('getent hosts ' + host).replace("\n", "")
	return outstr.split(" ")[0]

def is_alive(host):
	cmd = "ping -c 1 " + host
	outstr = shell.call_prog_as_is(cmd)
	if (outstr.find("64 bytes from") == -1):
		return False
	else:
		return True

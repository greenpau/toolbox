#!/usr/bin/python

import subprocess
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
	return shell.call_prog_as_is('whoami').replace("\n", "")

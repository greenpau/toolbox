#!/usr/bin/python

import os
import sys
sys.path.append("/usr/local/aos/pylib/system")

def abspath(path):
	dir = os.path.dirname(__file__)
	if os.path.isabs(path):
		return path
	else:
		path = os.path.join(dir, path)
		return path

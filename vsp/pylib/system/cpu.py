#!/usr/bin/python

import shell

def get_nprocs():
	output = shell.grep("cat /proc/cpuinfo", "processor")
	nprocs = 0
	for line in output:
		nprocs += 1
	return nprocs

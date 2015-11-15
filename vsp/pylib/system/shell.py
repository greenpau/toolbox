#!/usr/bin/python

sys.path.append("/usr/local/openvswitch/pylib/system")

import sys
import os
import subprocess
import select
import logger

def execute(args):
	''' Run a command and capture its output '''
	child = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=None)
	return child.communicate()[0]

def execute_hdr(header, args):
	print(header)
	cmdstr = "# " + ' '.join(args)
	print(cmdstr)
	print(execute(args))

def execute_log(logfd, args):
	''' Run a command and capture its output to logfd '''
	child = subprocess.Popen(args, stderr=subprocess.STDOUT,
				 stdout=logfd)
	logfd.flush()
	data = child.communicate()[0]
	rc = child.returncode
	return rc

def execute_raw(args):
	print(args)
	cmd = args.split()
	output = execute(cmd).splitlines()
	outline = ""
	for line in output:
		outline += line
		outline += "\n"
	return outline

def run_cmd(header, cmd, logfd):
	sys.stdout.write(header + " ... ")
	sys.stdout.flush()

	cmdstr = "# " + ' '.join(cmd)
	logger.write_log(logfd, cmdstr)
	rc = execute_log(logfd, cmd)
	if (rc == 0):
		print "done"
	else:
		print "failed"
	return rc

def grep(string, pattern):
	cmd = string.split()
	output = execute(cmd).splitlines()
	outline = ""
	for line in output:
		if (line.find(pattern) < 0):
			continue
		outline += line
		outline += "\n"
	return outline

def call_prog_as_is (cmd, wait_time=None) :
	proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
				 stderr=subprocess.PIPE, shell=True)
	read_set = [proc.stdout, proc.stderr]
	out = []
	err = []

	while read_set :
		timeout = True
		rlist, wlist, xlist = select.select (read_set, [], [], wait_time)
		if proc.stdout in rlist :
			timeout = False
			data = os.read (proc.stdout.fileno (), 1024)
			if data == "" :
				proc.stdout.close ()
				read_set.remove (proc.stdout)
			out.append (data)
		if proc.stderr in rlist :
			timeout = False
			data = os.read (proc.stderr.fileno (), 1024)
			if data == "" :
				proc.stderr.close ()
				read_set.remove (proc.stderr)
			err.append (data)
		if timeout :
			raise Exception ("timeout")

	proc.wait ()
	out = ''.join (out)
	err = ''.join (err)
	reply = (proc.returncode, out, err)
	if (reply == 0):
		print("Failed to execute: " + cmd)
	else :
		return reply[1].rstrip()


#!/usr/bin/python

import shell
import subprocess
import re
import os

def get_pid(procname):
	ps_ax = shell.execute(["ps", "ax"]).splitlines()
	for line in ps_ax:
		if line.find(procname) < 0:
			continue
		line_tok = line.split()
		return line_tok[0]
def all_procs():
	ps = subprocess.Popen("ps ax -o pid= -o args= ", shell=True, stdout=subprocess.PIPE)
	ps_pid = ps.pid
	output = ps.stdout.read()
	ps.stdout.close()
	ps.wait()
	return output, ps_pid

def proc_exists(proc_name):
	output, ps_pid = all_procs()
	for line in output.split("\n"):
		res = re.findall("(\d+) (.*)", line)
		if res:
			pid = int(res[0][0])
			this_proc = res[0][1].split(" ")[0:2]
			if ((proc_name in this_proc[0] or
			    (len(this_proc) > 1 and
			     (this_proc[0].find("sh") != -1 or
			      this_proc[0].find("python") != -1) and
			     proc_name in this_proc[1])) and
			     pid != os.getpid() and pid != os.getppid() and
			     pid != ps_pid):
				return True
	return False

def n_procs_by_name(proc_name):
	output, ps_pid = all_procs()
	n_procs = 0
	for line in output.split("\n"):
		res = re.findall("(\d+) (.*)", line)
		if res:
			pid = int(res[0][0])
			this_proc = res[0][1].split(" ")[0:2]
			if ((proc_name in this_proc[0] or
		            (len(this_proc) > 1 and
			     (this_proc[0].find("sh") != -1 or
			      this_proc[0].find("python") != -1) and
			     proc_name in this_proc[1])) and
			    pid != os.getpid() and pid != os.getppid() and
			    pid != ps_pid):
				n_procs = n_procs + 1
	return n_procs

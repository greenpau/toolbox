#!/usr/bin/python

import pexpect
import getpass
import time

import sys
sys.path.append("/usr/local/aos/pylib/wlan")

sys.path.append("/usr/local/aos/pylib/system")
import string_ext

class Device(object):
	hostname = None
	admin = "admin"
	admin_pass = "admins"
	support_pass = "B1ll10n5"
	src_user_password = None
	ssh_newkey = 'Are you sure you want to continue connecting'
	s = None
	t = None
	ssh_prompt_re = '\(.*\).*#'
	ssh_support_prompt_re = '.*support.*#'
	telnet_prompt_re = '\/.*#'
	telnet_enabled = False
	telnet_conn_refused = "Connection refused"
	telnet_port = "2323"
	crash_tarfile = "/flash/config/crash.tar"

	def __init__(self, hostname):
		self.hostname = hostname
		self.ssh()

	def ssh(self):
		s = pexpect.spawn('ssh ' + self.admin + '@' + self.hostname)
		i = s.expect([self.ssh_newkey, 'password:', pexpect.EOF,
			      pexpect.TIMEOUT], 1)
		s.sendline(self.admin_pass)
		s.expect(self.ssh_prompt_re)
		self.s = s

	def scp_to(self, src_host, src_user, src_path, dst_path):
		if self.s == None:
			self.ssh()
		cmd = "copy scp: " + src_host + " " + src_user + " " + src_path + " " + dst_path
		print cmd
		self.s.sendline(cmd)
		self.s.expect('.*Password:')
		if (self.src_user_password == None):
			self.src_user_password = getpass.getpass(src_user + '@' + src_host + '\'s password: ')
		self.s.sendline(self.src_user_password)
		self.s.expect(self.ssh_prompt_re, timeout=300)
		print self.s.before

	def scp_from(self, src_path, dst_user, dst_host, dst_path):
		if (self.s == None):
			self.ssh()
		cmd = "copy flash: " + src_path + " scp: " + dst_host + " " + dst_user + " " + dst_path
		print cmd
		self.s.sendline(cmd)
		self.s.expect('.*Password:')
		if (self.src_user_password == None):
			self.src_user_password = getpass.getpass(dst_user + '@' + dst_host + '\'s password: ')
		self.s.sendline(self.src_user_password)
		self.s.expect(self.ssh_prompt_re, timeout=300)
		print self.s.before

	def get_boot_partition(self):
		if self.s == None:
			self.ssh()
		self.s.sendline('show image version')
		self.s.expect(self.ssh_prompt_re)
		partition = ""
		output = self.s.before + self.s.after
		for l in output.splitlines():
			if l.find("Default boot") == -1:
				continue
			partition = l.split(":")[2].split(" ")[0]
			break
		return partition

	def get_boot_image_version(self):
		if self.s == None:
			self.ssh()
		self.s.sendline('show image version')
		self.s.expect(self.ssh_prompt_re)
		sw_vers = ""
		build_date = ""
		build_number = ""
		label = ""
		default_boot_seen = False
		output = self.s.before + self.s.after
		for l in output.splitlines():
			if l.find("Default boot") == -1:
				if (default_boot_seen == False):
					continue
			else:
				default_boot_seen = True
			if (l.find("----") != -1):
				if (default_boot_seen == True):
					break
			if (l.find("Software Version") != -1):
				sw_vers = l.split(":")[1].split(" ")[1:][1]
			if (l.find("Build number") != -1):
				build_number = l.split(":")[1]
			if (l.find("Label") != -1):
				label = l.split(":")[1]
			if (l.find("Built on") != -1):
				build_date_entry = l.split(":")[1:]
				build_date = " ".join(build_date_entry)
		return sw_vers, build_number, label, build_date

	def get_platid(self):
		if self.is_telnet_enabled() == False:
			self.enable_telnet()
			self.telnet()
		if self.t == None:
			print "Failed to telnet to " + self.hostname
			return
		cmd = "platid"
		self.t.sendline(cmd)
		self.t.expect(self.telnet_prompt_re)
		output = self.t.before + self.t.before
		platid = string_ext.sans_firstline(output).split("-")[0]
		return platid

	def reload(self):
		if self.s == None:
			self.ssh()
		cmd = "reload"
		print cmd
		self.s.sendline(cmd)
		self.s.expect("Do you really want to restart the system.*y/n.*:")
		self.s.sendline("y")
		self.s.expect(pexpect.EOF)
		self.s = None

	def __enable_support(self):
		self.s.sendline("support")
		self.s.expect('Password')
		self.s.sendline(self.support_pass)
		self.s.expect(self.ssh_support_prompt_re)

	def is_telnet_enabled(self):
		self.telnet()
		if (self.t != None):
			return True
		else:
			return False

	def enable_telnet(self):
		if self.telnet_enabled == True:
			return
		if self.s == None:
			self.login()
		sys.stdout.write("Enabling telnet access in controller " + self.hostname + ", please wait ... ")
		sys.stdout.flush()
		self.__enable_support()
		self.s.sendline("telnet shell")
		self.s.expect(self.ssh_support_prompt_re)
		self.telnet_enabled = True
		print "done"

	def telnet(self):
		cmd = "telnet " + self.hostname + " " + self.telnet_port
		t = pexpect.spawn(cmd)
		i = t.expect([self.telnet_conn_refused, 'User:', pexpect.EOF,
			      pexpect.TIMEOUT], 1)
		if (i == 1):
			self.telnet_enabled = True
			self.t = t
			self.t.sendline(self.admin + "\r")
			self.t.expect("Password:")
			self.t.sendline(self.admin_pass + "\r")
			self.t.expect("Support Password:")
			self.t.sendline(self.support_pass + "\r")
			self.t.sendline("\r\n")
			time.sleep(5)
			self.t.expect(self.telnet_prompt_re)

	def telnet_session(self):
		if self.is_telnet_enabled() == False:
			self.enable_telnet()
			self.telnet()
		if self.t == None:
			print "Failed to telnet to " + self.hostname
			return
		self.__telnet_shell()

	def __telnet_shell(self):
		sys.stdout.write(string_ext.sans_firstline(self.t.before))
		prompt = self.__telnet_get_prompt()
		sys.stdout.write(prompt)
		while True:
			if (self.__telnet_shell_cmd() == False):
				break

	def __telnet_shell_cmd(self):
		self.t.before = ""
		self.t.after = ""
		try:
			cmd = raw_input()
		except:
			return True
		prompt = self.__telnet_get_prompt()
		if cmd == "" or cmd == "\n":
			sys.stdout.write(prompt)
			return True
		if cmd == "exit":
			return False
		self.t.sendline(cmd)
		self.t.expect(self.telnet_prompt_re)
		outbuf = self.t.before + self.t.after
		sys.stdout.write(string_ext.sans_firstline(outbuf))
		return True

	def __telnet_get_prompt(self):
		self.t.sendline("pwd")
		self.t.expect(self.telnet_prompt_re)
		prompt = string_ext.sans_firstline(self.t.after)
		return prompt

	def mv(self, src_file, dst_file):
		if self.is_telnet_enabled() == False:
			self.enable_telnet()
			self.telnet()
		if self.t == None:
			print "Failed to telnet to " + self.hostname
			return
		cmd = "mv " + src_file + " " + dst_file
		print cmd
		self.t.sendline(cmd)
		self.t.expect(self.telnet_prompt_re)

	def gen_dp_core(self):
		if self.s == None:
			self.ssh()
		self.__enable_support()
		sys.stdout.write("Generating datapath coredump for " + self.hostname + ", please wait ... ")
		sys.stdout.flush()
		self.s.sendline('generate datapath coredump')
		self.s.expect(['.*Are you sure.*', pexpect.EOF,
			       pexpect.TIMEOUT])
		self.s.sendline('y')
		self.s.expect([self.ssh_support_prompt_re, pexpect.EOF,
			       pexpect.TIMEOUT])
		print "done"
		self.s = None

	def tar_crash(self):
		if self.s == None:
			self.ssh()
		self.s.sendline('tar crash')
		self.s.expect(self.ssh_prompt_re, timeout=300)
		return self.crash_tarfile_exists()

	def crash_tarfile_exists(self):
		self.enable_telnet()
		self.telnet()
		if self.t == None:
			print "Failed to telnet to " + self.hostname
			return False
		cmd = "ls -l " + self.crash_tarfile
		self.t.sendline(cmd)
		self.t.expect(self.telnet_prompt_re)
		output = self.t.before + self.t.after
		if output == "":
			print "No output for " + self.crash_tarfile
			return False
		if output.find(self.crash_tarfile) == -1:
			print "Unable to find " + self.crash_tarfile
			return False
		return True

	def scp_crash(self, dst_user, dst_host, dst_path):
		if (self.crash_tarfile_exists() == False):
			return
		self.scp_from(self.crash_tarfile, dst_user, dst_host, dst_path)
		return True

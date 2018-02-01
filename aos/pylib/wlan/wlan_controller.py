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
	telnet_prompt_re = '\/.*#'
	telnet_enabled = False
	telnet_conn_refused = "Connection refused"
	telnet_port = "2323"

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

	def scp(self, src_host, src_user, src_path, dst_path):
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

	def get_boot_partition(self):
		if self.s == None:
			self.ssh()
		self.s.sendline('show image version')
		self.s.expect(self.ssh_prompt_re)
		partition = ""
		for l in self.s.before.splitlines():
			if l.find("Default boot") == -1:
				continue
			partition = l.split(":")[2].split(" ")[0]
			break
		return partition

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
		self.s.sendline("support")
		self.s.expect('Password')
		self.s.sendline(self.support_pass)
		self.s.expect('support.*#')
		self.s.sendline("telnet shell")
		self.s.expect('.*support.*#')
		self.telnet_enabled = True

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
			sys.stdout.write("Enabling telnet access in controller " + self.hostname + ", please wait ... ")
			self.enable_telnet()
			self.telnet()
			print "done"
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
			sys.stdout.write("Enabling telnet access in controller " + self.hostname + ", please wait ... ")
			self.enable_telnet()
			self.telnet()
			print "done"
		if self.t == None:
			print "Failed to telnet to " + self.hostname
			return
		cmd = "mv " + src_file + " " + dst_file
		print cmd
		self.t.sendline(cmd)
		self.t.expect(self.telnet_prompt_re)

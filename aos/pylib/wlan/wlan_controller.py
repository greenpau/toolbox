#!/usr/bin/python

import pexpect
import getpass

import sys
sys.path.append("/usr/local/aos/pylib/wlan")

class Device(object):
	hostname = None
	admin = "admin"
	admin_pass = "admins"
	src_user_password = None
	ssh_newkey = 'Are you sure you want to continue connecting'
	s = None

	def __init__(self, hostname):
		self.hostname = hostname
		self.ssh()

	def ssh(self):
		s = pexpect.spawn('ssh ' + self.admin + '@' + self.hostname)
		i = s.expect([self.ssh_newkey, 'password:', pexpect.EOF,
			      pexpect.TIMEOUT], 1)
		s.sendline(self.admin_pass)
		s.expect('.*#')
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
		self.s.expect('.*#', timeout=300)
		print self.s.after

	def get_boot_partition(self):
		if self.s == None:
			self.ssh()
		self.s.sendline('show image version')
		self.s.expect('.*#')
		partition = ""
		for l in self.s.after.splitlines():
			if l.find("Default boot") == -1:
				continue
			partition = l.split(":")[2].split(" ")[0]
			break
		return partition

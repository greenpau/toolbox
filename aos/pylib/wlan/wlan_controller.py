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
	telnet_prompt_re = '[\/|\~].*#'
	telnet_enabled = False
	telnet_conn_refused = "Connection refused"
	telnet_port = "2323"
	crash_tarfile = "/flash/config/crash.tar"
	logs_tarfile = "/flash/config/logs.tar"

	def __init__(self, hostname):
		self.hostname = hostname
		self.ssh()

	def ssh(self):
		s = pexpect.spawn('ssh ' + self.admin + '@' + self.hostname)
		i = s.expect([self.ssh_newkey, 'password:', pexpect.EOF,
			      pexpect.TIMEOUT], timeout=60)
		if (i == 0):
			s.sendline("yes")
			s.expect("password:")
			s.sendline(self.admin_pass)
			s.expect(self.ssh_prompt_re)
		elif (i == 1) or (i == 2):
			s.sendline(self.admin_pass)
			s.expect(self.ssh_prompt_re)
		else:
			print "Failed to ssh to " + self.hostname
			exit(1)
		self.s = s
		self.s.sendline('no paging')
		self.s.expect(self.ssh_prompt_re)

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
				build_number = l.split(":")[1].split(" ")[1]
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

	def get_uptime(self):
		if self.s == None:
			self.ssh()
		self.s.sendline('show switch software')
		self.s.expect(self.ssh_prompt_re)
		output = self.s.before + self.s.after
		uptime = ""
		for l in output.splitlines():
			if (l.find("Switch uptime is") == -1):
				continue
			uptime = l.split("Switch uptime is")[1]
			break
		return uptime

	def get_switchrole(self):
		if self.s == None:
			self.ssh()
		self.s.sendline('show switchinfo')
		self.s.expect(self.ssh_prompt_re)
		output = self.s.before + self.s.after
		switchrole = ""
		for l in output.splitlines():
			if (l.find("switchrole") == -1):
				continue
			switchrole = l.split(":")[1]
			break
		return switchrole

	def get_nusers(self, name):
		if self.s == None:
			self.ssh()
		self.s.sendline('show user ap-name ' + name)
		self.s.expect(self.ssh_prompt_re)
		output = self.s.before + self.s.after
		nusers = 0
		for l in output.splitlines():
			if (l.find("User Entries") == -1):
				continue
			nusers = int(l.split(":")[1].split("/")[0])
			break
		return nusers

	def get_naps(self, type):
		if self.s == None:
			self.ssh()
		self.s.sendline('show ap ' + type)
		self.s.expect(self.ssh_prompt_re)
		output = self.s.before + self.s.after
		naps = ""
		for l in output.splitlines():
			if (l.find("Num APs") == -1):
				continue
			naps = l.split(":")[1]
			break
		return naps

	def get_aplines(self, type):
		if self.s == None:
			self.ssh()
		self.s.sendline('show ap ' + type)
		self.s.expect(self.ssh_prompt_re)
		output = self.s.before + self.s.after
		name_seen = False
		flags_seen = False
		aplines = []
		for l in output.splitlines():
			if (l.find("Name") == -1):
				if (name_seen == False):
					continue
			else:
				name_seen = True
				continue
			if (l.find("Flags:") == -1):
				if (flags_seen == False):
					if (l.find("----") == -1) and (l != ''):
						aplines.append(l)
					continue
			else:
				flags_seen = True
			break
		return aplines

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
		i = self.s.expect(['Password', 'Username', pexpect.EOF,
				   pexpect.TIMEOUT], timeout=60)
		if (i == 1):
			self.s.sendline(self.admin)
			self.s.expect("Please generate one time password", timeout=60)
			print
			if (self.s.before.find("Token: ") != -1):
				token = self.s.before.split("Token: ")[1].replace("\n", "")
				print "NOTE: support access needs to enabled with token " + token
			else:
				print "NOTE: support access needs to enabled"
			return False
		else:
			self.s.sendline(self.support_pass)
			self.s.expect(self.ssh_support_prompt_re)
		return True

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
			self.ssh()
		sys.stdout.write("Enabling telnet access in controller " + self.hostname + ", please wait ... ")
		sys.stdout.flush()
		if (self.__enable_support() == False):
			self.s = None
			return
		self.s.sendline("telnet shell")
		self.s.expect(self.ssh_support_prompt_re)
		self.telnet_enabled = True
		print "done"

	def telnet(self):
		cmd = "telnet " + self.hostname + " " + self.telnet_port
		t = pexpect.spawn(cmd)
		i = t.expect([self.telnet_conn_refused, 'User:', pexpect.EOF,
			      pexpect.TIMEOUT], timeout=60)
		if (i == 1):
			self.telnet_enabled = True
			self.t = t
			self.t.sendline(self.admin + "\r")
			self.t.expect("Password:")
			self.t.sendline(self.admin_pass + "\r")
			i = self.t.expect(["Support Password:", "Username",
					   pexpect.EOF, pexpect.TIMEOUT],
					  timeout=60)
			if (i != 0):
				self.t = None
				self.s = None
				return
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
		if (self.__enable_support() == False):
			return
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

	def tar_logs_with_tech_support(self):
		if self.s == None:
			self.ssh()
		self.s.sendline('tar logs tech-support')
		self.s.expect(self.ssh_prompt_re, timeout=500)
		return self.logs_tarfile_exists()

	def logs_tarfile_exists(self):
		return self.__file_exists(self.logs_tarfile)

	def scp_logs(self, dst_user, dst_host, dst_path):
		if (self.logs_tarfile_exists() == False):
			return
		self.scp_from(self.logs_tarfile, dst_user, dst_host, dst_path)
		return True

	def tar_crash(self):
		if self.s == None:
			self.ssh()
		self.s.sendline('tar crash')
		self.s.expect(self.ssh_prompt_re, timeout=300)
		return self.crash_tarfile_exists()

	def crash_tarfile_exists(self):
		return self.__file_exists(self.crash_tarfile)

	def __file_exists(self, file):
		self.enable_telnet()
		self.telnet()
		if self.t == None:
			print "Failed to telnet to " + self.hostname
			return False
		cmd = "ls -l " + file
		self.t.sendline(cmd)
		self.t.expect(self.telnet_prompt_re)
		output = self.t.before + self.t.after
		if output == "":
			print "No output for " + file
			return False
		if output.find(file) == -1:
			print "Unable to find " + file
			return False
		return True

	def scp_crash(self, dst_user, dst_host, dst_path):
		if (self.crash_tarfile_exists() == False):
			return
		self.scp_from(self.crash_tarfile, dst_user, dst_host, dst_path)
		return True

	def execute(self, cmd):
		if self.s == None:
			self.ssh()
		self.s.sendline(cmd)
		self.s.expect(self.ssh_prompt_re, timeout=300)
		output = self.s.before + self.s.after
		sys.stdout.write("CMD: ")
		sys.stdout.flush()
		print output

	def license_add(self, key, value):
		if self.s == None:
			self.ssh()
		if (self.__enable_support() == False):
			self.s = None
			return
		if (value != '') and (key != ''):
			self.s.sendline('genkey feature ' + key + ' ' + value)
		elif (key != ''):
			self.s.sendline('genkey feature ' + key)
		else:
			return
		i = self.s.expect(["KEY:", pexpect.EOF, pexpect.TIMEOUT],
				  timeout=30)
		if (i == 0):
			output = self.s.after + self.s.buffer
			lkeyelems = output.split("KEY:")
			if (len(lkeyelems) == 0):
				print "unable to find license key for {%s,%s}" % (key, value)
				return
			lkey = lkeyelems[1].lstrip().rstrip()
			self.s.sendline('license add ' + lkey)
			self.s.expect([pexpect.EOF, pexpect.TIMEOUT],
				      timeout=10)
			print "added license for {%s,%s -> %s}" % (key, value, lkey)
		else:
			print "failed to add license for {%s,%s}" %(key, value)

	def gen_ap_licenses(self):
		ap_prov_kv_basic = {
			'ap' : '2048',
			'acr-limit' : '2048',
			'pef-limit' : '2048',
			'rfp-limit' : '2048',
			'internal' : '',
			'pef-vpn' : '',
			'voice' : '',
			'firewall' : '',
		}
		for key,val in ap_prov_kv_basic.items():
			self.license_add(key, val)

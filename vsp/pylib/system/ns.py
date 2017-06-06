#!/usr/bin/python

import sys
import subprocess
import re
import uuid
from lxml import etree

# generic utility classes
sys.path.append("/usr/local/openvswitch/pylib/system")
import shell

class namespaces(object):
	xml_format = "\
	<domain type='kvm'>\
		<name>%s</name>\
		<uuid>%s</uuid>\
		<description>%s</description>\
		<memory>131072</memory>\
		<os>\
			<type arch='x86_64' machine='rhel6.2.0'>hvm</type>\
		</os>\
		<on_poweroff>destroy</on_poweroff>\
		<on_reboot>restart</on_reboot>\
		<on_crash>restart</on_crash>\
		<devices>\
			<emulator>/usr/libexec/qemu-kvm</emulator>\
			<interface type='bridge'>\
				<mac address='%s'/>\
				<source bridge='alubr0'/>\
				<virtualport type='openvswitch'/>\
				<target dev='%s'/>\
				<model type='rtl8139'/>\
			</interface>\
		</devices>\
	</domain>"
	vport_ovs_suffix = "veth1"
	vport_ns_suffix = "veth0"
	default_vmname = "vm1"

	def __init__(self, n_vms, n_brs):
		self.n_vms = n_vms
		self.n_brs = n_brs
		self.ports = []
		if n_vms:
			for i in range(1, n_vms + 1):
				self.ports.append("vm" + str(i))
		if n_brs:
			for i in range(1, n_brs + 1):
				self.ports.append("br" + str(i))

	def create_xml(self, vm_name, dev_name):
		if (vm_name == None):
			vm_name = self.default_vmname
		if (dev_name == None):
			dev_name = vm_name + "-" + self.vport_ovs_suffix
		cmd = 'ip netns exec '+vm_name+' ip a'
		output = subprocess.check_output(cmd, shell=True)
		uuid_str = str(uuid.uuid1())
		pattern = 'link/ether ([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})'
		match = re.search(pattern, output)
		m = match.group(0).split()
		mac = m[1]
		f = open('/var/tmp/' + dev_name + '.xml', 'w')
		f.write(self.xml_format % (dev_name, uuid_str, uuid_str, mac, dev_name))

	def setup(self):
		for p in self.ports:
			ovs_device = p + "-" + self.vport_ovs_suffix
			ns_device = p + "-" + self.vport_ns_suffix
			print "Setting up " + ovs_device + " and namespace " + ns_device
			shell.execute_cmdstr("ip netns add " + p)
			shell.execute_cmdstr("ip link add " + ns_device + " type veth peer name " + ovs_device)
			shell.execute_cmdstr("ip link set " + ns_device + " netns " + p)
			shell.execute_cmdstr("ip netns exec " + p + " ip link set " + ns_device + " up")
			shell.execute_cmdstr("ip netns exec " + p + " ip link set lo up")
			shell.execute_cmdstr("ip link set " + ovs_device + " up")
			shell.execute_cmdstr("ip netns exec " + p + " sysctl net.ipv4.ip_forward=1")
			self.create_xml(p, ovs_device)

	def destroy(self):
		for p in self.ports:
			ovs_device = p + "-" + self.vport_ovs_suffix
			print "Destroying " + ovs_device
			shell.execute_cmdstr("ip link delete " + ovs_device)
			shell.execute_cmdstr("ip netns del " + p)
			shell.execute_cmdstr("rm -rf /var/tmp/" + ovs_device + ".xml")

	def reinit(self):
		self.destroy()
		self.setup()

	def show(self, vm_name):
		for p in self.ports:
			if (vm_name != "all") and (vm_name != p):
				continue
			print "List of network interfaces in namespace " + p + ":"
			output = shell.execute_cmdstr("ip netns exec " + p + " ifconfig")
			print output

	def set_mac(self, port_name, mac):
		for p in self.ports:
			if (p != port_name):
				continue
			ns_device = p + "-" + self.vport_ns_suffix
			print "Setting mac " + mac + " for " + p + "::" + ns_device
			shell.execute_cmdstr("ip netns exec " + p + " ip link set dev " + ns_device + " address " + mac)

	def set_ip(self, port_name, ip, netmask):
		for p in self.ports:
			if (p != port_name):
				continue
			ns_device = p + "-" + self.vport_ns_suffix
			ipaddr = ip + "/" + netmask
			print "Setting ip " + ipaddr + " for " + p + "::" + ns_device
			shell.execute_cmdstr("ip netns exec " + p + " ip address add " + ipaddr + " dev " + ns_device)

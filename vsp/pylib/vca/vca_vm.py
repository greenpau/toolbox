#!/usr/bin/python

sys.path.append("/usr/local/openvswitch/pylib/system")
sys.path.append("/usr/local/openvswitch/pylib/ovs")
import shell
import ovs_ofproto

class VM(object):
	def __init__(self, ovs_path, br, vm_uuid, vm_iface, vm_ip_local,
		     vm_subnet, vm_netmask, vm_gw_ip, vm_mac, vm_xml,
		     vm_type, logfd):
		self.ovs_path = ovs_path
		self.appctl_path = ovs_path + "/ovs-appctl"
		self.br = br
		self.uuid = vm_uuid
		self.iface = vm_iface
		self.ip = vm_ip_local
		self.subnet = vm_subnet
		self.netmask = vm_netmask
		self.gw_ip = vm_gw_ip
		self.mac = vm_mac
		self.master_xml = vm_xml
		self.vm_type = vm_type
		self.logfd = logfd
		self.__create_work_xml()

	def __create_work_xml(self):
		self.work_xml = "/var/tmp/" + self.uuid + ".xml"
		xmlin = open(self.master_xml, 'r')

		xmlout = open(self.work_xml, 'w')
		for line in xmlin:
			inline = line.strip()
			if (inline.find("<uuid>") >= 0):
				outline = "<uuid>" + self.uuid + "</uuid>"
			elif (inline.find("<interface mac=") >= 0):
				outline = "<interface mac='" + self.mac + "' />"
			elif (inline.find("<mac address=") >= 0):
				outline = "<mac address='" + self.mac + "' />"
			elif (inline.find("<source bridge=") >= 0):
				outline = "<source bridge='" + self.br + "' />"
			elif (inline.find("<subnet address=") >= 0):
				outline = "<subnet address='" + \
					self.subnet + "' " + \
					"netmask='" + self.netmask + "' " + \
					"gateway='" + self.gw_ip + "' />"
			else:
			 	outline = inline
			outline += "\n"
			xmlout.write(outline)
		xmlin.close()
		xmlout.close()

	def define(self):
		cmd = [ "sudo", self.appctl_path, "vm/send-event", "define",
			self.work_xml, self.vm_type ]
		shell.run_cmd("Sending fake-VM define event of type: " + self.vm_type, cmd, self.logfd)

	def start(self):
		cmd = [ "sudo", self.appctl_path, "vm/send-event", self.uuid,
			"start" ]
		shell.run_cmd("Sending fake-VM start event", cmd, self.logfd)

	def destroy(self):
		cmd = [ "sudo", self.appctl_path, "vm/send-event", self.uuid,
			"destroy" ]
		shell.run_cmd("Sending fake-VM destroy event", cmd, self.logfd)

	def undefine(self):
		cmd = [ "sudo", self.appctl_path, "vm/send-event", self.uuid,
			"undefine" ]
		shell.run_cmd("Sending fake-VM undefine event", cmd, self.logfd)

	def show(self):
		cmd = [ "sudo", self.appctl_path, "vm/port-show" ]
		shell.execute_hdr("VM status", cmd)

	def vm_port(self):
		vm_port_no = 0
		if (self.vm_type == "bridge") :
			cmd = [ "sudo", self.appctl_path, "bridge/port-show" ]
		else :
			cmd = [ "sudo", self.appctl_path, "vm/port-show" ]
		vm_port_show = shell.execute(cmd).splitlines()
		for line in vm_port_show:
			if (line.find("Bridge:") < 0):
				continue
			line_tok = line.split()
			vm_port_no = line_tok[3]
			break
		return vm_port_no

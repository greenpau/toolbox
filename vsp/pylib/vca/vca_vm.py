#!/usr/bin/python

import sys

sys.path.append("/usr/local/openvswitch/pylib/system")
import shell

sys.path.append("/usr/local/openvswitch/pylib/ovs")
import ovs_ofproto

sys.path.append("/usr/local/openvswitch/pylib/vca")
import vca_json_config

class VM(object):
	vm_start_path = "/usr/local/openvswitch/tools/vca/vca-vm-start.sh"
	def __init__(self, ovs_path, br, vm_name, vm_uuid, vm_iface,
		     vm_ip_local, vm_subnet, vm_netmask, vm_gw_ip, vm_mac,
		     vm_xml, vm_type, logfd):
		self.ovs_path = ovs_path
		self.appctl_path = ovs_path + "/ovs-appctl"
		self.vsctl_path = ovs_path + "/ovs-vsctl"
		self.ofctl_path = ovs_path + "/ovs-ofctl"
		self.br = br
		self.name = vm_name
		self.uuid = vm_uuid
		self.iface = vm_iface
		self.ip = vm_ip_local
		self.subnet = vm_subnet
		self.netmask = vm_netmask
		self.gw_ip = vm_gw_ip
		self.mac = vm_mac
		self.master_xml = vm_xml
		self.type = vm_type
		self.logfd = logfd
		self.vm_port_cfg_file = "/var/tmp/port-cfg-" + vm_name + ".json"
		if (self.uuid != None):
			if (self.master_xml != None):
				self.__create_work_xml()
			else:
				self.port_cfg = vca_json_config.Port_Config_Vport(
						br, vm_type, vm_name, vm_iface,
						vm_mac, vm_uuid,
						self.vm_port_cfg_file, logfd)

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

	def add_port(self):
		if (self.port_cfg != None):
			self.port_cfg.generate()
			self.port_cfg.write()
			self.port_cfg.add()
		#cmd = [ self.vsctl_path, "add-port", self.br, self.iface ]
		#shell.run_cmd("Creating VM port in ovsdb", cmd, self.logfd)

	def del_port(self):
		cmd = [ self.vsctl_path, "del-port", self.br, self.iface ]
		shell.run_cmd("Deleting VM port from ovsdb", cmd, self.logfd)

	def add_membership(self, evpn_id):
		cmd = [ self.ofctl_path, "add-flow", self.br,
			'flow_type=route,type=' + self.type +
			',ip,flags=membership,evpn_id=' + str(evpn_id)+
			',interface=' + str(self.iface) +
			',vm_uuid=' + str(self.uuid) ]
		shell.run_cmd("Adding VM membership of " + self.name + " to evpn " + str(evpn_id),
			      cmd, self.logfd)
		return

	def add_acls(self):
		acls = ["pre", "post", "redirect" ]
		for acl in acls:
			cmd = [ self.ofctl_path, "add-flow", self.br,
				'flow_type=acl,type=' + self.type +
				',priority=0,flags=' + acl +
				',interface=' + self.iface +
				',vm_uuid=' + self.uuid +
				',action=allow' ]
			shell.run_cmd("Adding " + acl + " ACL for VM " + self.name,
			      cmd, self.logfd)
		return

	def add_routes(self, vrf_id, evpn_id):
		cmd = [ self.ofctl_path, "add-flow", self.br,
			"flow_type=route,type=" + self.type + ",flags=evpn" +
			",vrf_id=" + str(vrf_id) +
			",evpn_id=" + str(evpn_id) +
			",interface=" + self.iface +
			",vm_uuid=" + self.uuid +
			",dl_dst="+ self.mac ]
		shell.run_cmd("Adding evpn/vrf route to VM " + self.name,
			      cmd, self.logfd)
		cmd = [ self.ofctl_path, "add-flow", self.br,
			"flow_type=route,type=" + self.type +
			",flags=evpn-redirect,ip,vrf_id=" + str(vrf_id) +
			",evpn_id=" + str(evpn_id) +
			",nw_dst=" + self.ip ]
		shell.run_cmd("Adding evpn-redirect route to VM " + self.name,
			      cmd, self.logfd)
		cmd = [ self.ofctl_path, "add-flow", self.br,
			"flow_type=route,type=" + self.type +
			",flags=arp-route,ip,vrf_id=" + str(vrf_id) +
			",evpn_id=" + str(evpn_id) +
			",nw_dst=" + self.ip +
			",dl_dst=" + self.mac ]
		shell.run_cmd("Adding arp route to VM " + self.name,
			      cmd, self.logfd)
		cmd = [ self.ofctl_path, "add-flow", self.br,
			"flow_type=route,type=" + self.type +
			",flags=evpn,vrf_id=" + str(vrf_id) +
			",evpn_id=" + str(evpn_id) +
			",interface=" + self.iface +
			",vm_uuid=" + self.uuid +
			",dl_dst=" + self.mac ]
		shell.run_cmd("Adding mac route to VM " + self.name,
			      cmd, self.logfd)

	def add_qos(self,
		    ingress_rate, ingress_peak_rate, ingress_burst,
		    ingress_bum_rate, ingress_bum_peak_rate, ingress_bum_burst,
		    ingress_fip_rate, ingress_fip_peak_rate, ingress_fip_burst,
		    egress_class,
		    egress_fip_rate, egress_fip_peak_rate, egress_fip_burst):
		cmd = [ self.ofctl_path, "add-flow", self.br,
			"flow_type=qos,interface=" + self.iface +
			",type="+ self.type + ",vm_uuid=" + self.uuid +
			",ingress_rate=" + str(ingress_rate) +
			",ingress_peak_rate="+ str(ingress_peak_rate) +
			",ingress_burst=" + str(ingress_burst) +
			",ingress_bum_rate=" + str(ingress_bum_rate) +
			",ingress_bum_peak_rate=" + str(ingress_bum_peak_rate)+
			",ingress_bum_burst=" + str(ingress_bum_burst) +
			",ingress_fip_rate=" + str(ingress_fip_rate) +
			",ingress_fip_peak_rate=" + str(ingress_fip_peak_rate)+
			",ingress_fip_burst=" + str(ingress_fip_burst) +
			",egress_fip_rate=" + str(egress_fip_rate) +
			",egress_fip_peak_rate=" + str(egress_fip_peak_rate) +
			",egress_fip_burst=" + str(egress_fip_burst) +
			",egress_class=" + str(egress_class) ]
		shell.run_cmd("Adding qos route to VM " + self.name,
			      cmd, self.logfd)
		return

	def enable_mac_learning(self):
		cmd = [ self.ofctl_path, "add-flow", self.br,
			'flow_type=route,type=' + self.type +
			',flags=enable-learning,interface=' + self.iface +
			',vm_uuid='+ self.uuid ]
		shell.run_cmd("Enabling mac learning for VM " + self.name,
			      cmd, self.logfd)
		return

	def resolve(self, vm_list):
		for vm_name in vm_list:
			cmd = [ self.vm_start_path, vm_name ]
			shell.run_cmd("Resolving VM: " + vm_name,
				      cmd, self.logfd)

	def define(self):
		cmd = [ self.appctl_path, "vm/send-event", "define",
			self.work_xml, self.type ]
		shell.run_cmd("Sending fake-VM define event of type: " + self.type, cmd, self.logfd)

	def start(self):
		cmd = [ self.appctl_path, "vm/send-event", self.uuid,
			"start" ]
		shell.run_cmd("Sending fake-VM start event", cmd, self.logfd)

	def destroy(self):
		cmd = [ self.appctl_path, "vm/send-event", self.uuid,
			"destroy" ]
		shell.run_cmd("Sending fake-VM destroy event", cmd, self.logfd)

	def undefine(self):
		cmd = [ self.appctl_path, "vm/send-event", self.uuid,
			"undefine" ]
		shell.run_cmd("Sending fake-VM undefine event", cmd, self.logfd)

	def show(self):
		if (self.uuid != None) and (self.uuid != ""):
			cmd = [ self.appctl_path, "vm/port-show", self.uuid ]
		else:
			cmd = [ self.appctl_path, "vm/port-show" ]
		shell.execute_hdr("VM " + self.name + " port-show", cmd)

	def dump_flows(self):
		if (self.uuid != None) and (self.uuid != ""):
			cmd = [ self.appctl_path, "vm/dump-flows", self.uuid ]
		else:
			cmd = [ self.appctl_path, "vm/dump-flows" ]
		shell.execute_hdr("VM " + self.name + " dump-flows", cmd)

	def vm_port(self):
		vm_port_no = 0
		if (self.type == "bridge") :
			cmd = [ self.appctl_path, "bridge/port-show" ]
		else :
			cmd = [ self.appctl_path, "vm/port-show" ]
		vm_port_show = shell.execute(cmd).splitlines()
		for line in vm_port_show:
			if (line.find("Bridge:") < 0):
				continue
			line_tok = line.split()
			vm_port_no = line_tok[3]
			break
		return vm_port_no

	def set_vm_name(self, vm_name):
		self.name = vm_name

	def __parse_show_vm(self, vm_uuid, match_pattern, field):
		if (vm_uuid == None):
			cmd = [ self.appctl_path, "vm/port-show" ]
		else:
			cmd = [ self.appctl_path, "vm/port-show", vm_uuid ]
		vm_port_show = shell.execute(cmd).splitlines()
		content = None
		for line in vm_port_show:
			if (line.find(match_pattern) < 0):
				continue
			line_tok = line.split()
			content = line_tok[field]
			break
		return content

	def vm_uuid(self):
		return self.__parse_show_vm(None, self.name, 3)

	def port_name(self):
		vm_uuid = self.uuid()
		return self.__parse_show_vm(vm_uuid, "port-UUID", 3)

	def port_mac(self):
		vm_uuid = self.uuid()
		return self.__parse_show_vm(uuid, "MAC:", 5)

	def port_ip(self):
		vm_uuid = self.uuid()
		return self.__parse_show_vm(vm_uuid, "IP:", 1)

	def port_ofp_port(self):
		vm_uuid = self.uuid()
		return self.__parse_show_vm(vm_uuid, "port:", 3)

	def vrf_id(self):
		vm_uuid = self.uuid()
		return self.__parse_show_vm(vm_uuid, "vrf_id:", 1)

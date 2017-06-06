#!/usr/bin/python

import sys
sys.path.append("/usr/local/openvswitch/pylib/system")
sys.path.append("/usr/local/openvswitch/pylib/vca")
import time
import shell
import net
import vca_vrf
import vca_flows
import ovs_vport_tnl

class EVPN(vca_vrf.VRF):
	def __init__(self, ovs_path, br, logfd,
		     vrf_id, tnl_type, tnl_key,
		     evpn_id, evpn_tnl_key, evpn_subnet, evpn_netmask,
		     evpn_gw_ip, evpn_gw_mac, uplink_ip, vm_ip_local):
		self.ovs_path = ovs_path
		self.ofctl_path = ovs_path + "/ovs-ofctl"
		self.appctl_path = ovs_path + "/ovs-appctl"
		self.logfd = logfd
		self.br = br
		self.tnl = ovs_vport_tnl.Tunnel(self.ovs_path, self.br,
						None, None, "0.0.0.0", None,
						self.logfd, False)
		self.evpn_flows = vca_flows.Flows(self.ovs_path, self.br,
						  self.logfd)
		if (vrf_id != 0):
			vca_vrf.VRF.__init__(self, ovs_path, br, vrf_id,
					     tnl_type, tnl_key,
					     uplink_ip, logfd)
		if (evpn_id != 0):
			self.__init(evpn_id, evpn_tnl_key, tnl_type,
				    evpn_subnet, evpn_netmask,
				    evpn_gw_ip, evpn_gw_mac,
				    vm_ip_local)
			self.__add_evpn()

	def __init(self, evpn_id, evpn_tnl_key, tnl_type, evpn_subnet,
		   evpn_netmask, evpn_gw_ip, evpn_gw_mac, vm_ip_local):
		self.evpn_id = evpn_id
		if (vm_ip_local == None) or (vm_ip_local == ""):
			if (evpn_gw_ip != ""):
				val = evpn_gw_ip.split(".")
			self.evpn_subnet = evpn_subnet
			self.evpn_netmask = evpn_netmask
			self.evpn_gw_ip = evpn_gw_ip
			self.evpn_gw_mac = evpn_gw_mac
		else:
			val = vm_ip_local.split(".")
			self.evpn_gw_ip = val[0] + "." + val[1] + "." + val[2] + "." + "1"
			val = self.evpn_gw_ip.split(".")
			self.evpn_subnet = val[0] + "." + val[1] + "." + val[2] + "." + "0"
			self.evpn_gw_mac = "00:11:22:33:44:55"
			self.evpn_netmask = "255.255.255.0"
			self.evpn_flow_subnet = "255.255.255.0"
		if (tnl_type != ""):
			self.evpn_tnl_type = tnl_type
		else:
			self.evpn_tnl_type = "vxlan"
		self.evpn_tnl_key = evpn_tnl_key
		self.evpn_dhcp_range_lo = val[0] + "." + val[1] + "." + val[2] + ".91" 
		self.evpn_dhcp_range_hi = val[0] + "." + val[1] + "." + val[2] + ".93" 
		#self.evpn_dhcp_cfg = "dhcp_pool_enable,dhcp_pool_range=\"10.65.68.91-10.65.68.93\",dhcp_static_entry=\"00:00:00:00:00:11-10.65.68.93_00:00:00:00:00:22-10.65.68.92\""
		self.evpn_dhcp_cfg = "dhcp_pool_enable,dhcp_pool_range=" + self.evpn_dhcp_range_lo + "-" + self.evpn_dhcp_range_hi

	def __add_evpn(self):
		evpn_str = "evpn_id=" + self.evpn_id + \
			   ",vni_id=" + self.evpn_tnl_key + \
			   ",subnet=" + self.evpn_subnet + \
	       		   ",mask=" + self.evpn_netmask + \
			   ",gw_ip=" + self.evpn_gw_ip + \
			   ",gw_mac=" + self.evpn_gw_mac + \
			   ",flags=" + self.evpn_tnl_type + \
			   ",flags=" + self.evpn_dhcp_cfg
		cmd = [ self.ofctl_path, "-v", "add-evpn", self.br,
	       		self.vrf_id, evpn_str ]
		shell.run_cmd("Creating EVPN ID " + self.evpn_id,
			      cmd, self.logfd)

	def list_evpns(self):
		cmd = [ self.appctl_path, "evpn/show", self.br ]
		evpn_show_out = shell.execute(cmd).splitlines()
		evpn_list = []
		for line in evpn_show_out:
			if (line.find("evpn_id") < 0):
				continue
			line_tok = line.split()
			evpn_id = line_tok[1]
			evpn_list.append(evpn_id)
		return evpn_list

	def show(self):
		cmd = [ self.appctl_path, "evpn/show", self.br ]
		shell.execute_hdr("EVPN configuration", cmd)

	def reset(self):
		vrf_list = self.list_vrfs()
		for vrf_id in vrf_list:
			evpn_list = self.list_evpns()
			for evpn_id in evpn_list:
				cmd = [ self.ofctl_path, "del-evpn",
			       		self.br, vrf_id, "evpn_id=" + evpn_id ]
				shell.run_cmd("Deleting EVPN " + evpn_id,
					      cmd, self.logfd)

	def set_flows(self, vm_iface, vm_ip_local, vm_netmask, vm_subnet,
		      vm_mac, vm_gw_ip, vm_uuid, rtep_ip, vm_ip_remote,
		      vm_mac_remote, vm_type):
		self.evpn_flows.set_flow_evpn_membership(self.vrf_id,
							 self.evpn_id,
							 vm_iface, vm_uuid,
							 vm_type)
		time.sleep(2)
		self.evpn_flows.set_flow_evpn_route(self.vrf_id, self.evpn_id,
						    vm_iface, vm_ip_local,
						    vm_netmask, vm_subnet,
						    vm_mac, vm_uuid, vm_gw_ip,
						    vm_type, self.evpn_gw_ip)
		time.sleep(2)
		self.evpn_flows.set_flow_evpn_redirect(self.vrf_id,
						       self.evpn_id, vm_iface,
						       vm_ip_local, vm_netmask,
						       vm_mac, vm_uuid,
						       vm_gw_ip,
						       self.evpn_gw_ip,
						       self.evpn_flow_subnet)
		time.sleep(2)
		self.evpn_flows.set_flow_table_4_table_7()
		time.sleep(2)
		self.evpn_flows.set_flow_qos(vm_iface, vm_uuid)
		time.sleep(2)
		self.evpn_flows.set_flow_acl_ingress(vm_iface, vm_uuid, vm_type)
		time.sleep(2)
		self.evpn_flows.set_flow_acl_redirect(vm_iface, vm_uuid)
		time.sleep(2)
		self.evpn_flows.set_flow_arp_route(self.vrf_id, self.evpn_id,
						   vm_iface, vm_ip_local,
						   vm_mac, vm_uuid, vm_uuid,
						   self.evpn_gw_ip,
						   self.evpn_flow_subnet)
		time.sleep(2)
		self.evpn_flows.set_flow_dhcp_request(vm_iface, self.evpn_id,
			       			      vm_uuid, vm_ip_local)
		time.sleep(2)
		self.evpn_flows.set_flow_remote_route(self.vrf_id,
						      self.vrf_tnl_key,
						      self.evpn_id, vm_iface,
						      vm_ip_remote,
						      vm_mac_remote,
						      vm_type,
						      rtep_ip,
						      self.evpn_gw_ip,
						      self.evpn_flow_subnet)
		time.sleep(2)

	def __parse_evpn_show(self, match_pattern, field):
		cmd = [ self.appctl_path, "evpn/show", self.br ]
		evpn_show_out = shell.execute(cmd).splitlines()
		process_this_block = True
		toks = []
		for line in evpn_show_out:
			line_tok = line.split()
			if (line_tok == None) or (line_tok == []):
				continue
			if (line.find("evpn_id") >= 0):
				evpn_id = line_tok[1]
			if (line.find(match_pattern) < 0):
				continue
			out = line_tok[field]
			toks.append([evpn_id, out])
		return toks

	def list_evpn_ids_by_mode(self, mode):
		evpn_list = self.__parse_evpn_show("mode:", 1)
		out_list = []
		for entry in evpn_list:
			this_evpn = entry[0]
			this_mode = entry[1]
			if (mode != None):
				if (mode == this_mode):
					out_list.append(this_evpn)
			else:
				out_list.append(this_evpn)
		return out_list

	def list_vni_ids_by_mode(self, mode):
		mode_list = self.list_evpn_ids_by_mode(mode)
		evpn_list = self.__parse_evpn_show("vni_id:", 5)
		out_list = []
		for entry in evpn_list:
			this_evpn = entry[0]
			this_vni = entry[1]
			if (mode != None):
				for evpn in mode_list:
					if (this_evpn == evpn):
						out_list.append(this_vni)
			else:
				out_list.append(this_vni)
		return out_list

	def list_rteps_by_mode(self, mode, ip):
		vni_list = self.list_vni_ids_by_mode(mode)
		out_list = []
		for this_vni in vni_list:
			for this_tnl in self.tnl.list():
				if (this_tnl.find("ltep") >= 0):
					continue
				this_vni_val = this_vni.replace("0x", "")
				if this_tnl.find(this_vni_val) < 0:
					continue
				this_dst_ip_hex = this_tnl.replace("t", "").replace(this_vni_val, "")
				if (ip != None):
					ip_hex = net.ipaddr2hex(ip)
					if (ip_hex != this_dst_ip_hex):
						continue
					out_list.append([this_tnl, this_vni, ip])
				else:
					out_list.append([this_tnl, this_vni, None])
		return out_list

#!/usr/bin/python

import sys
import json

sys.path.append("/usr/local/openvswitch/pylib/system")
import json_config
import shell

class Json_Config_Vrfs(json_config.Json_Config):
	keys = {
		"vrf_id", "vrf_tnl_key",
	}
	attr = 'vrfs'
	def __init__(self, cfg_file, vlog):
		super(Json_Config_Vrfs, self).__init__(cfg_file, vlog)

	def read(self):
		return super(Json_Config_Vrfs, self).read(self.attr, self.keys)

	def count(self):
		return super(Json_Config_Vrfs, self).count(self.attr)

	def exists(self, key, value):
		if (key not in self.keys):
			return False
		return super(Json_Config_Vrfs, self).exists(self.attr,
							    self.keys, value)

	def search(self, pkey, pvalue, skey):
		if (pkey not in self.keys):
			return None
		if (super(Json_Config_Vrfs, self).exists(self.attr, self.keys,
							 pvalue) == True):
			return super(Json_Config_Vrfs, self).search(self.attr,
						self.keys, pkey, pvalue, skey)
		else:
			return None

class Json_Config_Evpns(json_config.Json_Config):
	keys = {
		"vrf_id", "evpn_id", "evpn_tnl_key", "tnl_type", "subnet",
		"mask", "gw_ip", "gw_mac",
	}
	attr = 'evpns'
	def __init__(self, cfg_file, vlog):
		super(Json_Config_Evpns, self).__init__(cfg_file, vlog)

	def read(self):
		return super(Json_Config_Evpns, self).read(self.attr, self.keys)

	def count(self):
		return super(Json_Config_Evpns, self).count(self.attr)

	def exists(self, key, value):
		if (key not in self.keys):
			return False
		return super(Json_Config_Evpns, self).exists(self.attr,
							     self.keys, value)

	def search(self, pkey, pvalue, skey):
		if (pkey not in self.keys):
			return None
		if (super(Json_Config_Evpns, self).exists(self.attr, self.keys,
							  pvalue) == True):
			return super(Json_Config_Evpns, self).search(self.attr,
						self.keys, pkey, pvalue, skey)
		else:
			return None

class Json_Config_Vms(json_config.Json_Config):
	keys = {
		"name", "interface", "evpn_id", "vrf_id", "ip", "mac", "uuid",
	}
	attr = 'vms'
	evpns_cfg_obj = None
	vrfs_cfg_obj = None
	def __init__(self, cfg_file, vlog, evpns_cfg_obj, vrfs_cfg_obj):
		self.evpns_cfg_obj = evpns_cfg_obj
		self.vrfs_cfg_obj = vrfs_cfg_obj
		super(Json_Config_Vms, self).__init__(cfg_file, vlog)

	def read(self):
		return super(Json_Config_Vms, self).read(self.attr, self.keys)

	def count(self):
		return super(Json_Config_Vms, self).count(self.attr)

	def vm_attrs(self, vm_cfg):
		valid = True
		name = ""
		for attrs in vm_cfg:
			for (k, v) in attrs.items():
				if (k == 'evpn_id'):
					if (self.evpns_cfg_obj.exists(k, v) == False):
						valid = False
						break
					evpn_id = str(v)
					evpn_tnl_key = self.evpns_cfg_obj.search('evpn_id', v, 'evpn_tnl_key')
					tnl_type = self.evpns_cfg_obj.search('evpn_id', v, 'tnl_type')
					evpn_subnet = self.evpns_cfg_obj.search('evpn_id', v, 'subnet')
					evpn_netmask = self.evpns_cfg_obj.search('evpn_id', v, 'mask')
					evpn_gw_ip = self.evpns_cfg_obj.search('evpn_id', v, 'gw_ip')
					evpn_gw_mac = self.evpns_cfg_obj.search('evpn_id', v, 'gw_mac')
				elif (k == 'vrf_id'):
					if (self.vrfs_cfg_obj.exists(k, v) == False):
						valid = False
						break
					vrf_id = str(v)
					vrf_tnl_key = self.vrfs_cfg_obj.search('vrf_id', v, 'vrf_tnl_key')
				elif (k == 'uuid'):
					uuid = v
				elif (k == 'name'):
					if (valid == True):
						name = v
				elif (k == 'interface'):
					interface = v
				elif (k == 'ip'):
					ip = v
				elif (k == 'mac'):
					mac = v
		return valid, name, interface, uuid, ip, mac, evpn_id, evpn_tnl_key, tnl_type, evpn_subnet, evpn_netmask, evpn_gw_ip, evpn_gw_mac, vrf_id, vrf_tnl_key

class Port_Config_Vport:
	nuage_port_config = '/usr/bin/nuage-port-config.pl'
	def __init__(self, br, type, name, interface, mac, uuid,
		     cfg_file, logfd):
		self.br = br
		self.type = type
		self.name = name
		self.interface = interface
		self.mac = mac
		self.uuid = uuid
		self.cfg_file = cfg_file
		self.logfd = logfd

	def generate(self):
		json_str = ""
		json_str = "{ \n \"hosts\" : \n\t["
		json_str += "\n\t\t{"
		json_str += ("\n\t\t\t\"%s\" : \"%s\" ," % ('type', self.type))
		json_str += ("\n\t\t\t\"%s\" : \"%s\" ," % ('name', self.name))
		json_str += ("\n\t\t\t\"%s\" : \"%s\" ," % ('interface', self.interface))
		json_str += ("\n\t\t\t\"%s\" : \"%s\" ," % ('mac', self.mac))
		json_str += ("\n\t\t\t\"%s\" : \"%s\" ," % ('uuid', self.uuid))
		json_str += ("\n\t\t\t\"%s\" : %d\n\t\t}," % ('vlan', 0))
		json_str = json_str[:-1]
		json_str += "\n\t]\n}"
		self.json_str = json_str

	def write(self):
		json_dict = eval(self.json_str)
		with open(self.cfg_file, 'w') as f:
			json.dump(json_dict, f, separators=(', ',':'),
				  sort_keys=True, indent = 4,
				  ensure_ascii=False)
		print "Generated port-config at " + self.cfg_file

	def add(self):
		cmd = [ self.nuage_port_config, '--secret', '--add',
			'--bridge', self.br, '--config', self.cfg_file ]
		shell.run_cmd("Executing " + self.nuage_port_config + " for " + self.name, cmd, self.logfd)


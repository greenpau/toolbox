#!/usr/bin/python

def set_vrf_defaults(home):
	vm_uuid = "003ac982-ad47-11e2-adfe-00224d69f9a9"
	vm_xml = "/usr/local/openvswitch/templates/vm.xml"
	vrf_id = str(100)
	evpn_id = str(200)
	return vm_uuid, vm_xml, vrf_id, evpn_id

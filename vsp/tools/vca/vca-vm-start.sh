#!/bin/bash
progname=`basename $0`
vm=$1
if [ -d /mv* ]; then
	testbed=`basename /mv*`
fi
if [ -z "${testbed}" -o -z "${vm}" ]; then
	echo "usage: ${progname} <vm> [<testbed>]"
	exit 1
fi
xml=/home/${testbed}/${vm}.xml
virsh define ${xml}
uuid=`grep -i uuid ${xml} | awk -F">" '{print $2}' | awk -F"<" '{print $1}'`
echo "Defining vm ${vm} from XML file ${xml}"
ovs-appctl vm/send-event define ${xml}
echo "Starting vm ${vm} with UUID ${uuid}"
ovs-appctl vm/send-event ${uuid} start

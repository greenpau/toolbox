#!/bin/bash
progname=`basename $0`
machine=$1
vm=$2
if [ -z "${machine}" -o -z "${vm}" ]; then
	echo "usage: ${progname} <machine> <vm>"
	exit 1
fi
virsh define /home/${machine}/${vm}.xml
uuid=`grep -i uuid /home/${machine}/${vm}.xml | awk -F">" '{print $2}' | awk -F"<" '{print $1}'`
echo "Starting vm ${vm} with UUID ${uuid} in machine ${machine}"
ovs-appctl vm/send-event ${uuid} start

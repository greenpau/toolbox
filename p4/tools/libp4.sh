#!/bin/bash

get_branch() {
	local branch
	branch=`adu mappings | tail -2 | grep -v ^$ | awk '{print $1}' | awk -F/ '{print $NF}'`
	echo "${branch}"
}

get_clid_list_pending() {
	local user=$1
	local client=$2
	clid_list="`p4 changes -u ${user} | grep ${client} | grep pending | awk '{print $2}' | sort -u`"
	echo $clid_list
}

get_clid_n_pending() {
	local user=$1
	local client=$2
	clid_list_pending="`get_clid_list_pending ${user} ${client}`"
	n_clid_pending=`echo ${clid_list_pending} | awk 'END{print NF}'`
	echo ${n_clid_pending}
}

get_clid_flist() {
	local clid=$1
	local branch=$2
	out="`p4 describe -du ${clid} | grep //depot | grep ${branch}`"
	for e in $out; do
		if [ "$e" == "..." ] || [ "$e" == "add" ] || [ "$e" == "edit" ]; then
			continue
		fi
		echo $e | awk -F\# '{print $1}' | awk -F${branch}/ '{print $2}'
	done
}

get_clid_most_recent() {
	local user=$1
	local client=$2
	clid_list_pending="`get_clid_list_pending ${user} ${client}`"
	clid=`echo ${clid_list_pending} | awk '{print $NF}'`
	echo ${clid}
}

describe_clid() {
	local clid=$1
	if [ -z "${clid}" ]; then
		return 1
	fi
	tmp_outfile=/var/tmp/describe_clid.$$
	echo "Changelist ID: ${clid}" > ${tmp_outfile}
	p4 describe -du ${clid} >> ${tmp_outfile}
	echo "" >> ${tmp_outfile}
	echo "Diff:" >> ${tmp_outfile}
	echo "" >> ${tmp_outfile}
	p4 opened -c ${clid} | sed -e 's/#.*//' | p4 -x - diff -du >> ${tmp_outfile}
	less ${tmp_outfile}
	rm -rf ${tmp_outfile}
}

get_flist_nochangelist() {
	local user=$1
	local client=$2
	local branch=$3

	pending_clid_list=`get_clid_list_pending ${user} ${client}`
	flist="`p4 opened | awk '{print $1}' | awk -Fdepot '{print $2}' | awk -F'#' '{print $1}' | awk -F${branch}/ '{print $2}'`"
	new_flist=
	for clid in ${pending_clid_list}; do
		this_clid_flist=`get_clid_flist ${clid} ${branch}`
		for f in ${flist}; do
			echo "${this_clid_flist}" | grep $f > /dev/null
			if [ $? -ne 0 ]; then
				new_flist="$f ${new_flist}"
			fi
		done
	done
	echo ${new_flist}
}

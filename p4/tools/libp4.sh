#!/bin/bash

get_branch() {
	local branch
	branch=`adu mappings | tail -2 | grep -v ^$ | awk '{print $1}' | awk -F/ '{print $NF}'`
	echo "${branch}"
}


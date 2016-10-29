#!/bin/bash

get_options()
{
	progname=`basename $0`
	export log=/tmp/${progname}.log

	if [ -z "$1" ]; then
		return
	fi
	while [ $# -ne 0 ]; do
		case "$1" in
		--no-converged-repos)
			export CONVERGED_REPOS=0
			shift
			;;
		-a|--alt-repo)
			export ALT_REPO=$2
			shift; shift
			if [ -z "${ALT_REPO}" ]; then
				echo "${progname}: missing alternate repo name"
				usage 1
			fi
			;;
		-A|--add)
			export ADD="$2"
			shift;shift
			if [ -z "${ADD}" ]; then
				echo "${progname}: missing alternate repo name"
				usage 1
			fi
			;;
		-b|--branch)
			export BRANCH=$2
			shift; shift
			if [ -z "${BRANCH}" -o "${BRANCH}" = "master" ]; then
				echo "${progname}: missing or bad branch name"
				usage 1
			fi
			;;
		-c|--component)
			export COMP=$2
			shift; shift
			if [ -z "${COMP}" ]; then
				echo "${progname}: missing component name"
				usage 1
			fi
			;;
		-D|--detail)
			DETAIL=1
			shift
			;;
		-F|--force)
			export FORCE="--force"
			shift
			;;
		-f|--file)
			export FILE=$2
			shift; shift
			if [ -z "${FILE}" ]; then
				echo "${progname}: missing file name"
				usage 1
			fi
			;;
		-L|--list)
			export LIST=1
			shift
			;;
		-n|--name)
			export SB=$2
			shift; shift
			if [ -z "${SB}" ]; then
				echo "${progname}: missing or bad sandbox name"
				usage 1
			fi
			;;
		-p|--parent)
			export PARENT_BRANCH=$2
			shift; shift
			if [ -z "${PARENT_BRANCH}" ]; then
				echo "${progname}: missing parent branch name"
				usage 1
			fi
			;;
		-R|--remove)
			export REMOVE=1
			shift
			;;
		-h|--help)
			usage 0 ;;
		*)	if [ -z "${ARGLIST}" ]; then
				ARGLIST="$1"
			else
				ARGLIST="${ARGLIST} $1"
			fi
			shift
			;;
		esac
	done
}

git_branch()
{
	local b=`git branch | grep -e '*' | awk '{print $2}'`
	echo ${b}
}

git_clone()
{
	local proj=$1 target=$2
	local repo_name=${proj}.git

	mkdir -p ${target}
	printf "Cloning ${server}:${repo_name} ... "
	git clone ${user}@${server}:${repo_name} ${target} >> ${log} 2>&1
	echo "done"
}

git_checkout()
{
	local branch=$1

	printf "Checking out branch ${branch} ... "
	if [ -n "${branch}" ]; then
		git checkout -b ${branch} >> ${log} 2>&1
	else
		git checkout master >> ${log} 2>&1
	fi
	echo "done"
}

git_iterate()
{
	local project base_project this_component comp_path old_repo new_repo ar
	local branch
	local func=$1

	if [ -z ${func} ]; then
		return
	fi

	for project in ${REPOS[@]}; do
		#
		# whatever is specified in ALT_REPO, use it to override
		# what is mentioned in REPOS array entry
		#
		if [ -n "${ALT_REPO}" ]; then
			for ar in ${ALT_REPO}; do
				old_repo=`echo ${ar} | awk -F: '{print $1}'`
				new_repo=`echo ${ar} | awk -F: '{print $2}'`
				if [ ${old_repo} = "${project}" ]; then
					project="${new_repo}"
					break
				fi
			done
		fi
		base_project=${project}
		this_component=`basename ${project}`
		if [ -n "${COMP}" -a "${COMP}" != "all" -a \
				      ${this_component} != "${COMP}" -a \
		     "${COMP}" != ${base_project} ]; then
			continue
		fi
		(
			if [ ${this_component} = "ovs" -o \
			     ${this_component} = "ovs-2.3" -o \
			     ${this_component} = "ovs-2.5" -o \
			     ${this_component} = "ovs-2.6" -o \
			     ${this_component} = "dpdk" ]; then
				if [ ! -d "VCA/ovs" -a \
				     ! -d "VCA/ovs-2.3" -a \
				     ! -d "VCA/ovs-2.5" -a \
				     ! -d "VCA/ovs-2.6" -a \
				     ! -d "VCA/vrs/third-party/dpdk" ]; then
					continue
				fi
				this_component=${base_project}
			fi
			if [ -d ${this_component} ]; then
				cd ${this_component}
			fi
			eval ${func} ${this_component}
		)
	done
}

apply_main()
{
	local func=$1
	local this_component project

	if [ "${COMP}" != "main" ]; then
		return
	fi
	(
		project="main"
		this_component=`basename ${project}`
		cd ${linux_sbhead}/${SANDBOX}
		eval ${func} ${this_component}
	)
}

get_sb() {
	envfile=.sandbox-env
	dir=`pwd`
	while [ ! -f $dir/$envfile ]; do
		dir=`dirname $dir`
		if [ $dir == "/" ]; then
			echo ""
			return
		fi
	done
	echo $dir
}

get_repo_name()
{
	local repo_project repo project=$1

	if [ ! -d .git ]; then
		echo 
		return
	fi
	repo_project=`git remote -v | grep fetch | grep origin | awk '{print $2}'`
	echo ${repo_project} | grep http > /dev/null 2>&1
	if [ $? -eq 0 ]; then
		repo_dir=`dirname ${repo_project}`
		repo_base=`basename ${repo_project}`
		repo=`basename ${repo_dir}`/${repo_base}
	else
		repo=`echo ${repo_project} | awk -F: '{print $2}'`
	fi
	repo_project=${repo}
#	repo_project=`grep url ${config_file} | grep ${project} | awk -F: '{print $2}'`
	repo=`echo ${repo_project} | sed -e "s/.git//g" | sed -e "s/^\/\.//g"`
	echo ${repo}
}

is_valid_repo()
{
	local repo

	if [ ! -d .git ]; then
		echo 0
		return
	fi
	repo=`get_repo_name ${project}`
	if [ "${project}" = "VCA/ovs" -o \
	     "${project}" = "VCA/ovs-2.3" -o \
	     "${project}" = "VCA/ovs-2.5" -o \
	     "${project}" = "VCA/ovs-2.6" -o \
	     "${project}" = "VCA/vrs/third-party/dpdk" ]; then
		echo 1
	elif [ "${repo}" != "${project}" ]; then
		echo 0
	else
		echo 1
	fi
}

if [ -z "${linux_sbhead}" ]; then
	sbpath=`get_sb`
	if [ -n "${sbpath}" ]; then
		linux_sbhead=`dirname ${sbpath}`
		SANDBOX=`basename ${sbpath}`
	fi
fi
if [ -z "${linux_sbhead}" ]; then
	echo "Not inside a sandbox"
	exit 1
fi
cd ${linux_sbhead}

#
# All global variables
#
gitenv_file=${linux_sbhead}/${SANDBOX}/.git-env
REPOS=( \
	sabyasse/toolbox \
	VCA/VCA \
	VCA/vrs/third-party/dpdk \
	VCA/ovs \
	VCA/ovs-2.3 \
	VCA/ovs-2.5 \
	VCA/ovs-2.6 \
	SROS/TiMOS \
	SDVPN/NSG \
	Juniper/contrail-vrouter \
	Juniper/contrail-controller \
)

user=git
server=github.mv.usa.alcatel.com
sshkey=~/.ssh/mv-git
config_file=.git/config
export CONVERGED_REPOS=1

if [ -f ${gitenv_file} ]; then
	. ${gitenv_file}
fi

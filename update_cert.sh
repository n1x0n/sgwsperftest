#!/bin/bash

START=$(date +%s.%N)

# Variables
SCRIPTNAME=$( basename $0 )
BASEDIR="${HOME}"
FILE=""
DRYRUN=0

declare -a on_exit_items

function on_exit()
{
    for i in "${on_exit_items[@]}"
    do
        debug "on_exit: $i"
        eval $i
    done
}

function add_on_exit()
{
    local n=${#on_exit_items[*]}
    on_exit_items[$n]="$*"
    if [[ $n -eq 0 ]]; then
        debug "Setting trap"
        trap on_exit EXIT
    fi
}

debug() {
    if [[ $DEBUG = 1 ]]
    then
        timestamp "DEBUG: $*" 2<&1
    fi
}

timestamp() {
        END=$(date +%s.%N)
        DIFF=$(echo "$END - $START" | bc)
        echo "[$DIFF]   $*"
}

usage() {
	echo "Usage: $SCRIPTNAME storagenode port certfile"
}

debug "Starting"

# We need a directory to operate on.
if [[ -z $TEMP ]]
then
        TEMP=/tmp
fi
TEMPDIR="${TEMP}/$( basename $0 ).$$.tmp"
mkdir "$TEMPDIR"
add_on_exit rm -rf "$TEMPDIR"


# Script
NODE=$1
PORT=$2
FILE=$3

if [[ -z $FILE ]]
then
	usage
	exit 1
fi

debug "Downloading certificate from ${NODE}:${PORT}."
openssl s_client -showcerts -connect ${NODE}:${PORT} </dev/null > $TEMPDIR/dummy.pem
if [[ $? = 0 ]]
then
	debug "Certificate downloaded successfully, copying to ${FILE}."
	cp $TEMPDIR/dummy.pem $FILE
fi


# Done
debug "Done"

#!/usr/bin/env python

from __future__ import print_function

"""
This script can be used to output a list of keys
from a bucket.
"""

############################################################
# Modules
############################################################
import time
import socket
import sys
import os
from contextlib import closing
import json
import boto3
import boto3.session
import requests
import configparser
import multiprocessing as mp
import re
import random
from subprocess import Popen, PIPE, STDOUT


############################################################
# Global Variables
############################################################
timer_start = time.perf_counter()
download_start = time.perf_counter()
test_start = int(time.time())
counter = 0
totalsize = 0
certfile = ""
resultlist = []
threshold = 0.5
longesttime = 0


############################################################
# Helper Functions
############################################################
def usage():
    print("Usage: download_data.py CONFIGFILE")


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def debug(message):
    """Prints debug messages.."""
    DEBUG=False
    if "DEBUG" in os.environ:
        if os.environ["DEBUG"] == "0":
            DEBUG=False
        else:
            DEBUG=True
    if not DEBUG:
        return
    now = time.perf_counter()
    elapsed = now - timer_start
    eprint("[%f] %s" % (elapsed, message))
    return


def abort(message="Unknown error"):
    """Aborts with message."""
    now = time.perf_counter()
    elapsed = now - timer_start
    eprint("[%f] ABORT: %s" % (elapsed, message))
    quit(1)


def quit(exitcode=0):
    cleanup()
    debug("Exiting with code %s." % exitcode)
    sys.exit(exitcode)


def cleanup():
    """Called once in quit/abort, used to cleanup."""
    debug("Cleaning up")
    return True


############################################################
# Functions
############################################################
def get_options(config):
    if not (len(sys.argv) > 1):
        usage()
        quit(1)

    try:
        config.read(sys.argv[1])
    except Exception as e:
        abort("Error when reading configuration: %s" % e.message)


def main():
    """Main entrypoint for the script"""

    config = configparser.ConfigParser()
    get_options(config)

    baseurl = "%s://%s:%s" % (
        config['perftest']['protocol'],
        config['perftest']['endpoints'].split(",")[0],
        config['perftest']['port'],
	)

    global certfile
    certfile = config['perftest']['certfile']

    print("Getting file list from: %s" % config['perftest']['bucketname'])
    print("Storage nodes: %s" % config['perftest']['endpoints'])

    # We need to pass everything that boto3 needs into
    # each sub process.
    session = boto3.session.Session(aws_access_key_id=config['perftest']['access_key'], aws_secret_access_key=config['perftest']['secret_key'])
    s3 = ""
    if config['perftest']['protocol'] == "https":
        s3 = session.resource(service_name='s3', endpoint_url=baseurl, verify=config['perftest']['certfile'])
    else:
        s3 = session.resource(service_name='s3', endpoint_url=baseurl)
    bucket = s3.Bucket(config['perftest']['bucketname'])

    print("Getting list of objects.")
    print("Writing list to %s." % config['perftest']['filelist'])
    f = open(config['perftest']['filelist'], "w")
    counter = 0
    for thisfile in bucket.objects.all():
        f.write("%s\n" % thisfile.key)
        counter += 1
    f.close

    print("Found %s objects." % counter)

    quit()


############################################################
# Start the script
############################################################
if __name__ == '__main__':
    main()



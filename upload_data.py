#!/usr/bin/env python

from __future__ import print_function

"""
This script takes a directory and uploads all files into
StorageGRID Webscale.
"""

############################################################
# Modules
############################################################
import time
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


############################################################
# Global Variables
############################################################
timer_start = time.perf_counter()
upload_start = time.perf_counter()
counter = 0
totalsize = 0


############################################################
# Helper Functions
############################################################
def usage():
    print("Usage: upload_data.py CONFIGFILE")


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


def upload(endpoint,access_key,secret_key,bucketname,certfile,datadir,key):
    session = boto3.session.Session(aws_access_key_id=access_key, aws_secret_access_key=secret_key)
    s3 = session.resource(service_name='s3', endpoint_url=endpoint, verify=certfile)
    data = open(("%s/%s" % (datadir, key)), 'rb')
    s3.Bucket(bucketname).put_object(Key=key, Body=data)
    obj = s3.Object(bucketname, key)
    obj.wait_until_exists()
    size = obj.content_length

    #print("%s: Uploaded %s" % (mp.current_process().name, key))

    return(int(size))


def collect_result(result):
    global upload_start
    global counter
    global totalsize
    counter += 1
    totalsize += result
    if not ( counter % 100 ):
        now = time.perf_counter()
        elapsed = now - timer_start
        objs_per_sec = "%.0f" % (counter / elapsed)
        megabytes_per_sec = "%.2f" % (totalsize / elapsed / 1024 / 1024)
        print("%s files uploaded in %.1f secs. %s objects/s, %s MB/s" % (counter, elapsed, objs_per_sec, megabytes_per_sec))


def main():
    """Main entrypoint for the script"""

    config = configparser.ConfigParser()
    get_options(config)

    baseurl = "%s://%s:%s" % (
        config['perftest']['protocol'],
        config['perftest']['endpoint'],
        config['perftest']['port'],
	)


    print("Uploading to host: %s/%s" % (baseurl,config['perftest']['bucketname']))
    print("Files uploaded from: %s" % config['perftest']['datadir'])

    workers = int(config['perftest']['workers'])

    # We need to pass everything that boto3 needs into
    # each sub process.
    files = []
    for (_, _, filenames) in os.walk(config['perftest']['datadir']):
        files.extend(filenames)
        break

    work = []
    for thisfile in files:
        dummy = [baseurl,
            config['perftest']['access_key'],
            config['perftest']['secret_key'],
            config['perftest']['bucketname'],
            config['perftest']['certfile'],
            config['perftest']['datadir'],
            thisfile
        ]
        work.append(dummy)

    pool = mp.Pool(processes=workers)
    for key in work:
        pool.apply_async(upload, key, callback=collect_result)
    pool.close()
    pool.join()

    global upload_start
    global counter
    global totalsize

    now = time.perf_counter()
    elapsed = now - timer_start
    objs_per_sec = "%.0f" % (counter / elapsed)
    megabytes_per_sec = "%.2f" % (totalsize / elapsed / 1024 / 1024)
    print("SUMMARY: %s files uploaded in %.1f secs. %s objects/s, %s MB/s" % (counter, elapsed, objs_per_sec, megabytes_per_sec))


    quit()


############################################################
# Start the script
############################################################
if __name__ == '__main__':
    main()



#!/usr/bin/env python

from __future__ import print_function

"""
This script takes a bucket and downloads all objects
from StorageGRID Webscale.
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
import random
from subprocess import Popen, PIPE, STDOUT


############################################################
# Global Variables
############################################################
timer_start = time.perf_counter()
download_start = time.perf_counter()
counter = 0
totalsize = 0
certfile = ""


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


def download(url):
    #global certfile
    #headers = {'Accept-Encoding': 'identity'}
    #r = requests.get(url, headers=headers, stream=True, verify=certfile)
    #size = r.headers['Content-length']
    #if r.status_code == 200:
    #    with open('/dev/null', 'wb') as f:
    #        for chunk in r:
    #            f.write(chunk)
    #return(int(size))

    size = 0
    with Popen(["/usr/bin/wget", "--no-check-certificate", "-O", "/dev/null", "%s" % url], stdout=PIPE, stderr=STDOUT) as p:
        while p.poll() is None:
            row = p.stdout.readline().decode()
            m = re.match(r"^Length: (\d+)", row)
            if (m):
                size = int(m.group(1))
        
    return(size)


def collect_result(result):
    global download_start
    global counter
    global totalsize
    counter += 1
    totalsize += result
    if not ( counter % 10 ):
        now = time.perf_counter()
        elapsed = now - download_start
        objs_per_sec = "%.0f" % (counter / elapsed)
        megabytes_per_sec = "%.2f" % (totalsize / elapsed / 1024 / 1024)
        print("%s files downloaded in %.1f secs. %s objects/s, %s MB/s" % (counter, elapsed, objs_per_sec, megabytes_per_sec))


def main():
    """Main entrypoint for the script"""

    config = configparser.ConfigParser()
    get_options(config)

    baseurl = "%s://%s:%s" % (
        config['perftest']['protocol'],
        config['perftest']['endpoint'],
        config['perftest']['port'],
	)

    global certfile
    certfile = config['perftest']['certfile']

    print("Downloading from: %s/%s" % (baseurl,config['perftest']['bucketname']))

    workers = int(config['perftest']['workers'])

    # We need to pass everything that boto3 needs into
    # each sub process.
    session = boto3.session.Session(aws_access_key_id=config['perftest']['access_key'], aws_secret_access_key=config['perftest']['secret_key'])
    s3 = session.resource(service_name='s3', endpoint_url=baseurl, verify=config['perftest']['certfile'])
    bucket = s3.Bucket(config['perftest']['bucketname'])

    policy = {
      "Statement":[
            {
                "Sid":"AddPerm",
                "Effect":"Allow",
                "Principal": "*",
                "Action":["s3:ListBucket"],
                "Resource":["urn:sgws:s3:::" + config['perftest']['bucketname']]
            },
        {
          "Sid":"AddPerm",
          "Effect":"Allow",
          "Principal": "*",
          "Action":["s3:GetObject"],
          "Resource":["urn:sgws:s3:::" + config['perftest']['bucketname'] + "/*"]
        }
      ]
    }
    bucket.Policy().put(Policy=json.dumps(policy))

    print("Getting list of objects.")
    work = []
    for thisfile in bucket.objects.all():
        dummy = ["%s/%s/%s" % (baseurl, config['perftest']['bucketname'], thisfile.key)]
        work.append(dummy)

    print("Found %s objects." % len(work))
    print("Shuffling list to randomize download pattern.")
    random.shuffle(work)

    numobjs =  int(config['perftest']['number_of_objects']) 
    work = work[0:numobjs]
    print("Downloading %s objects." % len(work))
    print("Starting download.")

    pool = mp.Pool(processes=workers)
    global download_start
    download_start = time.perf_counter()
    for key in work:
        pool.apply_async(download, key, callback=collect_result)
    pool.close()
    pool.join()

    global counter
    global totalsize

    now = time.perf_counter()
    elapsed = now - download_start
    objs_per_sec = "%.0f" % (counter / elapsed)
    megabytes_per_sec = "%.2f" % (totalsize / elapsed / 1024 / 1024)
    print("SUMMARY: %s files downloaded in %.1f secs. %s objects/s, %s MB/s" % (counter, elapsed, objs_per_sec, megabytes_per_sec))


    quit()


############################################################
# Start the script
############################################################
if __name__ == '__main__':
    main()



#!/usr/bin/env python

"""
"""
import sys
import os
import re
import string
import subprocess
import tempfile
import getopt
import time
import shutil
import traceback
import requests
import xml.etree.ElementTree as ET
import python_cipres.pyjavaproperties as Props
import python_cipres.client as CipresClient

sys.stdout.flush()

def cipresjob(argv):
    """
    cipresjob.py OPTIONS 

    Where OPTIONS are:

    -h 
        help
    -l
        list all the user's jobs 
    -j JOBHANDLE 
        choose a job to act upon.  If no other action (like download) is selected, shows the job's status.
    -d 
        download job results to a subdirectory of the current directory named JOBHANDLE.
        Use with -j to specify the job.
    -v 
        verbose (use with -l to get a verbose job listing)

    For example:
        cipresjob.py -l
            list the user's jobs
        cipresjob.py -j JOBHANDLE
            shows status of the job whose jobhandle is JOBHANDLE
        cipresjob.py -j JOBHANDLE -d
            download's results of the job whose jobhandle is JOBHANDLE
    """
    jobHandle = None
    verbose=False
    action="status"
    options, remainder = getopt.getopt(argv[1:], "j:hldv")
    for opt, arg in options:
        if opt in ("-j"):
            jobHandle = arg
        elif opt in ("-h"):
            print(cipresjob.__doc__)
            return 0
        if opt in ("-l"):
            action="list"
        elif opt in ("-d"):
            action="download"
        elif opt in ("-v"):
            verbose=True

    properties = CipresClient.Application().getProperties()
    client = CipresClient.Client(properties.APPNAME, properties.APPID, properties.USERNAME, properties.PASSWORD, properties.URL)

    if action != "list" and not jobHandle:
        print(cipresjob.__doc__)
        return 1
    try:
        if action == "list":    
            jobs = client.listJobs()
            for job in jobs:
                if verbose:
                    job.show(messages=True)
                else:
                    job.show(messages=False)
            return 0
        if action == "status":
            job = client.getJobStatus(jobHandle)
            job.show(messages=True)
            return 0
        if action == "download":
            job = client.getJobStatus(jobHandle)
            if not os.path.exists(job.jobHandle):
                os.mkdir(job.jobHandle)
            if job.isDone():
                print "Downloading final results to %s" % (os.path.abspath(job.jobHandle))
                job.downloadResults(directory=job.jobHandle, final=True)
            else:
                print "Job isn't finished. Downloading working dir files to %s" % (os.path.abspath(job.jobHandle))
                job.downloadResults(directory=job.jobHandle, final=False)
            return 0 
        print(cipresjob.__doc__)
        return 1
    except CipresClient.ValidationError as ve:
        print ve.asString()
        return 2
    except CipresClient.CipresError as ce:
        print "CIPRES ERROR: %s" % ( ce )
        return 2
    except requests.exceptions.RequestException as e:
        print "CONNECTION ERROR: %s" % (e)
        return 2
        
# Call this with the complete sys.argv array
def tooltest(argv):
    """
        tooltest.py TEMPLATE_DIRECTORY validate|run
        
        Where TEMPLATE_DIRECTORY is the name of a directory that contains the job's input data files and
        two property files named testInput.properties and testParam.properties.

        validate
            Ask's the REST API whether the job is valid.  If valid, prints to stdout, the command line that 
            would be run on the execution host if the job were submitted to run.  If invalid, prints an
            error message that explains which fields have errors.

        run
            Submits the job to the REST API, waits for it to complete, and downloads the results to
            a subdirectory of the current directory whose name is the jobhandle (i.e, starts with "NGBW-"))
    """

    if not argv or len(argv) < 3:
        print tooltest.__doc__
        return 1
    template = argv[1]
    action = argv[2]
    if not os.path.isdir(template):
        print "%s is not a valid TEMPLATE_DIRECTORY" % (template)
        print tooltest.__doc__
        return 1
    if action != "validate" and action != "run":
        print "second argument must be either validate or run"
        print tooltest.__doc__
        return 1

    properties = CipresClient.Application().getProperties()
    client = CipresClient.Client(properties.APPNAME, properties.APPID, properties.USERNAME, properties.PASSWORD, properties.URL)
    try:
        if action == "validate":
            job = client.validateJobTemplate(template)
            job.show()
        else:
            job = client.submitJobTemplate(template)
            job.show(messages="true")
            print "Waiting for job to complete ..."
            job.waitForCompletion()
            if not os.path.exists(job.jobHandle):
                os.mkdir(job.jobHandle)
            print "Downloading results to %s" % (os.path.abspath(job.jobHandle))
            job.downloadResults(directory=job.jobHandle)
    except CipresClient.ValidationError as ve:
        print ve.asString()
        return 2
    except CipresClient.CipresError as ce:
        print "CIPRES ERROR: %s" % ( ce )
        return 2
    except requests.exceptions.RequestException as e:
        print "CONNECTION ERROR: %s" % (e)
        return 2
    return 0


def main():
    return cipresjob(sys.argv)
    
if __name__ == "__main__":
    sys.exit(main())
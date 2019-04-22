#!/usr/bin/env python

import sys
import time
import os.path
import subprocess as sp

# Globals

PROCESS_STATES = ["held", "ready", "running", "done"]

# Utils

def countPlus(s):
    """Return the number of + characters at the beginning of string `s'."""
    np = 0
    for c in s:
        if c == '+':
            np += 1
        else:
            return np
        
class Job(object):
    name = ""
    proc = None
    pid = None
    cmdline = ""
    status = None
    retcode = 0
    dependents = []
    
    def __init__(self, cmdline, name=None, status="ready"):
        self.cmdline = cmdline
        if name:
            self.name = name
        else:
            self.name = cmdline.split(" ")[0]
        self.retcode = 0
        self.status = status
        self.dependents = []

    def start(self):
        self.proc = sp.Popen(self.cmdline, shell=True)
        self.pid = self.proc.pid
        self.status = "running"
        return self.pid

    def check(self):
        r = self.proc.poll()
        if r is None:
            return False
        self.status = "done"
        self.retcode = r
        return True
    
class JobMan(object):
    jobs = []
    delay = 1
    maxjobs = 0
    filenames = []
    _njobs = 0
    _nrunning = 0
    _ndone = 0
    _log = False
    
    def __init__(self, maxjobs=0, delay=1):
        self.jobs = []
        self.delay = delay
        self.maxjobs = maxjobs
        self._njobs = 0
        self._nrunning = 0
        self._ndone = 0

    def usage(self):
        sys.stderr.write("""jobman.py - Simple job manager

Usage: jobman.py [options] [filenames...]

This program executes the specified subprocesses, waiting for them to 
terminate. The commands to be executed can be read from one or more files, 
or from standard input, if no file argument is specified. Options:

-d D | Poll proocesses every D seconds (default: {}).
-m M | Run at most M concurrent processes (default: no limit).
        -l   | Enable logging (to standard error).

Each command line can be preceded by one or more '+' characters (up to 20),
indicating that the corresponding job should be executed after a previous 
one has terminated. For example, given the following commands:

cmd1
+cmd2
++cmd3
cmd4
+cmd5

cmd1 and cmd4 will be executed immediately, cmd2 will be executed after cmd1, 
cmd5 will be executed after cmd4, and cmd3 will be executed after cmd3.

When all jobs are terminated, the program writes two integer numbers to 
standard output, separated by a tab: the total number of jobs executed,
and the number of jobs that returned an exit status of 0. The return
status of the jobman process is the highest exit status returned by any
of the jobs. For example, if the program executes three jobs, one of 
which returns an exit status of 3, then: 

$ jobman jobs.txt
3 2
$ echo $?
3

(c) 2019, Alberto Riva.

""".format(self.delay))
        return False
        
    def parseArgs(self, args):
        if "-h" in args or "--help" in args:
            return self.usage()
        prev = ""
        for a in args:
            if prev == "-d":
                self.delay = int(a)
                prev = ""
            elif prev == "-m":
                self.maxjobs = int(a)
                prev = ""
            elif a == "-l":
                self._log = True
            elif a in ["-d", "-m"]:
                prev = a
            else:
                if os.path.isfile(a):
                    self.filenames.append(a)
        return True

    def initialize(self):
        if self.filenames:
            for f in self.filenames:
                self.initFromFile(f)
        else:
            self.initFromStream(sys.stdin)    
        
    def log(self, string, *args):
        if self._log:
            sys.stderr.write(string.format(*args) + "\n")
        
    def addJob(self, job):
        self._njobs += 1
        job.name = str(self._njobs)
        self.jobs.append(job)
        self.log("Job #{}: {}", job.name, job.cmdline)

    def initFromFile(self, filename):
        with open(filename, "r") as f:
            self.initFromStream(f)

    def initFromStream(self, f):
        stack = [None]*20       # Can we have more than 20-deep dependencies?
        for line in f:
            line = line.rstrip()
            if line:
                if line[0] == '#':
                    continue
                nplus = countPlus(line)
                line = line[nplus:]
                job = Job(line)
                self.addJob(job)
                if nplus > 0:
                    job.status = "held"
                    parent = stack[nplus-1]
                    parent.dependents.append(job)
                stack[nplus] = job

        self.log("{} jobs defined.", self._njobs)

    def showJobs(self):
        for j in self.jobs:
            if j.status != "held":
                self.showJob(j, 0)

    def showJob(self, job, ind):
        sys.stdout.write("+"*ind + job.cmdline + " (" + job.status + ")\n")
        ind += 1
        for dep in job.dependents:
            self.showJob(dep, ind)
            
    def hasRoom(self):
        """Return True if there's room to start a new job."""
        return self.maxjobs == 0 or self._nrunning < self.maxjobs

    def startJob(self, job):
        job.start()
        self._nrunning += 1
        
    def run(self):
        while True:
            # Check if any running jobs are done
            for j in self.jobs:
                # self.log("Checking job #{}, {}", j.name, j.status)
                if j.status == "running" and j.check():
                    self.log("Job #{} terminated.", j.name)
                    self._nrunning += -1
                    self._ndone += 1
                    self.log("Jobs running: {}", self._nrunning)
                    for dep in j.dependents:
                        dep.status = "ready"
                        self.log("Job #{} now ready.", dep.name)

            # Check if we have room to start new jobs and
            # that we have new jobs that can be started
            for j in self.jobs:
                if j.status == "ready" and self.hasRoom():
                    self.startJob(j)
                    self.log("Job #{} started.", j.name)
                    self.log("Jobs running: {}", self._nrunning)
                    
            if self._ndone == self._njobs:
                self.log("All jobs terminated.")
                break

            time.sleep(self.delay)

    def report(self):
        nzero = 0
        maxret = 0
        for j in self.jobs:
            if j.retcode == 0:
                nzero += 1
            elif j.retcode > maxret:
                maxret = j.retcode

        sys.stdout.write("{}\t{}\n".format(self._njobs, nzero))
        sys.exit(maxret)
        
def test():
    JM = JobMan(delay=5, maxjobs=2)
    JM.addJob(Job("sleep 30"))
    JM.addJob(Job("sleep 50"))
    JM.addJob(Job("sleep 20"))
    JM.addJob(Job("sleep 40"))
    JM.addJob(Job("sleep 10"))
    return JM

if __name__ == "__main__":
    args = sys.argv[1:]
    JM = JobMan()
    if JM.parseArgs(args):
        JM.initialize()
        # JM.showJobs()
        JM.run()
        JM.report()
    

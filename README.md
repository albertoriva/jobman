# Jobman - Minimal job manager

Jobman is a simple program to run several commands concurrently. It can
be used as a replacement for full-featured schedulers such as Slurm or PBS,
when you want to run multiple processes on a single node with multiple cores.

Jobman offers the following features:

- Commands to be executed can be read from one or more files, or from standard input;
- Allows controlling the maximum number of processes that can run at the same time;
- Provides a visual display of running, waiting, and completed processes;
- Jobs can be dependent on other jobs;
- Keeps track of which jobs terminated successfully and which ones didn't (based on the job's return code);
- Generates a full report containing job results and execution times.

## Usage:

```
jobman.py [options] [filenames...]
```

Options:

Option     | Meaning
-----------|--------
-h, --help | Print help message
-d D       | Poll processes every D seconds (default: 5).
-m M       | At most M jobs can run concurrently (default: no limit).
-r R       | Write report to file R.
-q         | Do not display job map while running (see below).
-l         | Enable logging (to standard error).

## Job definition

A job definition file contains commands to be executed in parallel. Each
command should fit on a single line, and should do no I/O operations. You 
can use ; to concatenate multiple commands into a single job, and redirection
operators (< and >). Empty lines and lines starting with # are
ignored. If multiple filenames are listed on the jobman command line, the
program will execute all commands contained in them, as if the files were
concatenated.

## Dependent jobs

Each command line can be preceded by one or more '+' characters (up to 20),
indicating that the corresponding job should be executed after a previous 
one, its parent, has terminated. For example, given the following commands:

```
cmd1
+cmd2
++cmd3
cmd4
+cmd5
```

cmd1 and cmd4 will start immediately, cmd2 will be executed after cmd1, 
cmd3 will be executed after cmd2, and cmd5 will be executed after cmd4.

By default, a dependent job will run after its parent terminates regardless 
of the parent's exit status. If the -x option is specified, instead, a dependent
job will only run if its parent returned a 0 exit status. This can be used
to prevent dependent jobs from running if their parent failed.

Note that a job can only depend on a job that appears in the same job definition
file.

## Job map

While running, the program will print a string showing the state of all jobs
to standard error (unless -q is specified). Each job is represented by a single
character, and the characters for all jobs are printed consecutively, in order,
on a single line. The string is printed only when the status of at least one job
changes. The characters used in the string are are:

Char | Meaning
-----|--------
 . | job ready to run.
 w | dependent job waiting for its parent to complete.
 R | job running.
 &ast; | job completed with return code 0.
 ! | job completed with non-zero return code.
 ? | Job invalidated because its parent had non-zero return code.


## Return values

When all jobs are terminated, the program writes three numbers to standard
output, separated by a tab: the total number of jobs executed, the number
of jobs that returned an exit status of 0, and the total elapsed time in
seconds. The return status of the jobman process is the highest exit status
returned by any of the jobs. For example, if the program executes three jobs,
one of which returns an exit status of 3, then: 

```bash
$ jobman jobs.txt
3    2    123.45
$ echo $?
3
```

## Reports

The user can request a full report with the -r option. The report
is a tab-delimited file with one line for each job and three columns:

  - Job number (starting at 1)
  - Return code
  - Job duration in seconds.

Additionally, the program can write the commands that were unsuccessful (ie,
had a non-zero return code) to a new job definition file, allowing the failed
commands to be re-run. This is accomplished with the -u option, followed by
the name of the new job definition file.

## Limitations

Contrary to real schedulers like Slurm or PBS, Jobman has no way of knowing how
much memory a job will require. It is up to the user to ensure that the number
of concurrent processes is not large enough to exhaust the available memory.

Jobman can only find out that a process is done when it checks it, and this 
happens every D seconds (where D is 60 by default and can be changed
with the -d option). This means that the job duration reported in the report
file (-r option) and the overall one provided at the end of execution will always
be multiples of D. For example, if D is 10 seconds and job execution takes two
seconds, its duration will still be reported as 10 seconds. To avoid this, make D
much smaller than the expected duration of the fastest process.

## Examples

Assume the file test.jobs contains the following:

```
sleep 10
+sleep 20
++sleep 10; exit 1
+sleep 15

sleep 10; exit 3
+sleep 20
```

Then:

```
$ ./jobman.py -d 2 -r report.txt -u failed.txt test.jobs
RwwwRw
*RwR!R
**R*!*
**!*!*
6	4	40.047388
```

This shows that of the six processes, four completed successfully and
two had a non-zero error code. Execution of all commands took 40 seconds. 
The report.txt file now contains:

```
1       0       10.013428
2       0       20.027645
3       1       10.009108
4       0       16.02026
5       3       10.011195
6       0       20.022374
```

and the failed.txt file contains:

```
sleep 10; exit 1

sleep 10; exit 3
```

If the -x option is supplied, the output instead would be:

```bash
$ ./jobman.py -d 2 -r report.txt -u failed.txt test.jobs
RwwwRw
*RwR!?
*Rw*!?
**R*!?
**!*!?
6	4	40.325167
```
indicating that job #6 did not run, since its parent (job #5) returned
a non-zero return code.

The -u option can be used to automatically re-run failed jobs. For example,
assume that each job in the file badjobs.txt has a small chance of failing. The
following code will re-run failed jobs until all are successful:

```bash
cp badjobs.txt to-run.txt
while 1;
do
  jobman.py -u failed.txt to-run.txt
  if [ "$?" == 0 ];
  then
    break
  fi
  cp failed.txt to-run.txt
done
```

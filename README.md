# jobman
Minimal job manager

Jobman is a simple program to run several commands concurrently. The
commands can be read from one or more files or from standard input. It
has the following features:

- Allows controlling the maximum number of processes that can run at the same time;
- Provides a visual display of running, waiting, and completed processes;
- Jobs can be dependent on other jobs;
- Keeps track of which jobs terminated successfully and which ones didn't;
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
command should fit on a single line (you can use ; to concatenate multiple
commands into a single job). Empty lines and lines starting with # are
ignored. If multiple filenames are listed on the jobman command line, the
program will execute all commands contained in them, as if the files were
concatenated.

## Dependent jobs

Each command line can be preceded by one or more '+' characters (up to 20),
indicating that the corresponding job should be executed after a previous 
one (its parent) has terminated. For example, given the following commands:

```
cmd1
+cmd2
++cmd3
cmd4
+cmd5
```

cmd1 and cmd4 will be executed immediately, cmd2 will be executed after cmd1, 
cmd5 will be executed after cmd4, and cmd3 will be executed after cmd3.

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
 . | job ready to run
 w | dependent job waiting for its parent to complete
 R | job running
 &ast; | job completed with return code 0
 ? | job completed with non-zero return code


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
# jobman
Minimal job manager

Jobman is a simple program to run several commands concurrently. The
commands can be read from one or more files or from standard input.

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
-l         | Enable logging (to standard error).

## Dependent jobs

Each command line can be preceded by one or more '+' characters (up to 20),
indicating that the corresponding job should be executed after a previous 
one has terminated. For example, given the following commands:

```
cmd1
+cmd2
++cmd3
cmd4
+cmd5
```

cmd1 and cmd4 will be executed immediately, cmd2 will be executed after cmd1, 
cmd5 will be executed after cmd4, and cmd3 will be executed after cmd3.

## Return values

When all jobs are terminated, the program writes two integer numbers to 
standard output, separated by a tab: the total number of jobs executed,
and the number of jobs that returned an exit status of 0. The return
status of the jobman process is the highest exit status returned by any
of the jobs. For example, if the program executes three jobs, one of 
which returns an exit status of 3, then: 

```bash
$ jobman jobs.txt
3 2
$ echo $?
3
```

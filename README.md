# paramiko-sample

sample code to use paramiko

## How to use

### Install

```bash
(paramiko) $ python setup.py develop
(paramiko) $ paramiko-ssh --help
usage: paramiko-ssh [-h] [--async] [--verbose] hosts [hosts ...] command

positional arguments:
  hosts       set remote hosts
  command     set command

optional arguments:
  -h, --help  show this help message and exit
  --async     enable asynchronous mode
  --verbose   enable verbose mode
```

### Run command via ssh

Run command with sync mode via ssh.

```bash
(paramiko) $ paramiko-ssh $host whoami
2019-11-08 18:13:44,989 INFO start
2019-11-08 18:13:45,388 INFO connected: $host
2019-11-08 18:13:45,464 INFO $host stdout:
t2y
2019-11-08 18:13:45,466 INFO status code: 0
2019-11-08 18:13:45,467 INFO end
```

Run command asynchronously with [asyncio](https://docs.python.org/3/library/asyncio.html) via ssh.

```bash
(paramiko) $ paramiko-ssh --async $host whoami
2019-11-08 18:15:04,713 INFO start
2019-11-08 18:15:05,096 INFO connected: $host
2019-11-08 18:15:07,223 INFO $host: status=0, whoami
2019-11-08 18:15:07,224 INFO stdout:
t2y

2019-11-08 18:15:07,224 INFO end
```

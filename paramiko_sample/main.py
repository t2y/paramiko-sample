import argparse
import asyncio
import logging
import sys
from enum import Enum

from .remote import remote_batch_run
from .remote import RemoteHost
from .utils import log


async def remote_batch(q, tasks, **kwargs):
    results = await remote_batch_run(tasks, **kwargs)
    for (status, stdout, stderr), (host, command) in results:
        if status != 0:
            log.error(f'failed to run {host}: {status}')
            log.error(command)
            log.error(f'stderr: {stderr.decode(sys.stderr.encoding)}')

        log.info(f'{host}: status={status}, {command}')
        log.info(f'stdout:\n{stdout.decode(sys.stdout.encoding)}')
        q.put_nowait(status)


def run_async(args, credential=None, password=None):
    tasks = tuple((host, args.command) for host in args.hosts)
    event_loop = asyncio.get_event_loop()
    q = asyncio.Queue(maxsize=len(tasks), loop=event_loop)
    coroutine = remote_batch(
        q, tasks, credential=credential, password=password, interval=1)
    event_loop.run_until_complete(coroutine)

    success = True
    while not q.empty():
        status = q.get_nowait()
        if status != 0:
            success = False
    return success


def run_sync(args):
    results = []
    for _host in args.hosts:
        with RemoteHost(_host) as host:
            exit_status = host.run(args.command)
        log.info('status code: %d' % exit_status)
        results.append(exit_status == 0)
    return all(results)


def parse_argument():
    parser = argparse.ArgumentParser()
    parser.set_defaults(
        hosts=[],
        is_async=False,
        verbose=False,
    )

    # optional arguments
    parser.add_argument(
        '--async', action='store_true', dest='is_async',
        help='enable asynchronous mode'
    )
    parser.add_argument(
        '--verbose', action='store_true',
        help='enable verbose mode'
    )

    # positional arguments
    parser.add_argument('hosts', nargs='+', help='set remote hosts')
    parser.add_argument('command', help='set command')

    args = parser.parse_args()
    return args


def main():
    class ExitStatus(Enum):
        SUCCESS = 0
        ERROR = 1

    args = parse_argument()
    if args.verbose:
        log.setLevel(logging.DEBUG)

    log.info('start')
    log.debug(args)

    if args.is_async:
        success = run_async(args)
    else:
        success = run_sync(args)

    log.info('end')
    return ExitStatus.SUCCESS.value if success else ExitStatus.ERROR.value


if __name__ == '__main__':
    sys.exit(main())

import asyncio
import io
import os
import sys
from getpass import getpass
from functools import lru_cache

from paramiko import ProxyCommand
from paramiko.agent import AgentRequestHandler
from paramiko.client import AutoAddPolicy
from paramiko.client import SSHClient
from paramiko.config import SSHConfig
from paramiko.rsakey import RSAKey

from .utils import log


class Credential:

    def __init__(self, data, username=None, sudo=False, passphrase=None):
        self._data = data
        self.username = username
        self.sudo = sudo
        self.passphrase = passphrase
        self.pkey = None
        if data is not None:
            self.pkey = RSAKey(file_obj=io.StringIO(data), password=passphrase)

    @property
    @lru_cache(maxsize=1)
    def connect_param(self):
        return {
            'pkey':  self.pkey,
            'username': self.username,
            'password': self.passphrase,
        }


class RemoteHost:

    PATH_CONFIG = '~/.ssh/config'

    def __init__(self, host, credential=None,
                 stdout_queue=None, stderr_queue=None):
        self._password = None
        self.host = host
        self.credential = credential
        self.stdout_queue = stdout_queue
        self.stderr_queue = stderr_queue
        self.client = SSHClient()
        self.client.set_missing_host_key_policy(AutoAddPolicy())
        self.config = SSHConfig()
        self.forward_agent = False
        self.parse_config_if_exists()

    def __enter__(self):
        self.client.load_system_host_keys()
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.disconnect()

    def parse_config_if_exists(self):
        path = os.path.expanduser(self.PATH_CONFIG)
        if os.path.exists(path):
            with open(path) as f:
                self.config.parse(f)

    def connect(self):
        host_config = self.config.lookup(self.host)
        log.debug('ssh-config: %s' % host_config)

        forwardagent = host_config.get('forwardagent')
        if forwardagent is not None and forwardagent == 'yes':
            self.forward_agent = True
            log.debug('forwarding agent is enabled')

        param = {
            'sock': None,
            'timeout': 10.0,
        }

        proxy_command = host_config.get('proxycommand')
        if proxy_command is not None:
            param['sock'] = ProxyCommand(proxy_command)

        if self.credential is not None:
            param.update(self.credential.connect_param)

        self.client.connect(self.host, **param)
        log.info('connected: %s' % self.host)

    def disconnect(self):
        self.client.close()

    @property
    def password(self):
        if self._password is None:
            self._password = getpass('Password: ').encode('ascii') + b'\n'
        return self._password

    @password.setter
    def password(self, value):
        self._password = value

    def is_active(self):
        transport = self.client.get_transport()
        return transport is not None and transport.is_active()

    async def run_async(self, command, stdin_param=None, get_pty=False,
                        interval=10, callback=None, buff_size=1024):
        if not self.is_active():
            log.error('ssh connection is not active')
            return

        transport = self.client.get_transport()
        channel = transport.open_session()

        if self.forward_agent:
            AgentRequestHandler(channel)

        if get_pty:
            channel.get_pty()
            channel.set_combine_stderr(True)

        channel.exec_command(command.encode(sys.stdout.encoding))

        if stdin_param is not None:
            stdin = channel.makefile('wb', -1)
            stdin.write(stdin_param)
            stdin.flush()

        while not channel.exit_status_ready():
            if callback is not None:
                callback(channel)
            await asyncio.sleep(interval)

        if channel.exit_status != 0:
            log.warn('%s exit status is not zero: %d' % (
                     self.host, channel.exit_status))

        stdout = stderr = b''
        while channel.recv_ready():
            stdout += channel.recv(buff_size)
            await asyncio.sleep(1)
        if stdout and self.stdout_queue is not None:
            s = stdout.decode(sys.stdout.encoding)
            self.stdout_queue.put_nowait(s)

        while channel.recv_stderr_ready():
            stderr += channel.recv_stderr(buff_size)
            await asyncio.sleep(1)
        if stderr and self.stderr_queue is not None:
            s = stderr.decode(sys.stderr.encoding)
            self.stderr_queue.put_nowait(s)

        return channel.exit_status, stdout, stderr

    async def sudo_async(self, command, password=None, **kwargs):
        cmd = 'sudo %s' % command
        if password is not None:
            self.password = password
        return await self.run_async(
            cmd, stdin_param=self.password, get_pty=True, **kwargs)

    def run(self, command, stdin_param=None, combine_stderr=False, **kwargs):
        if not self.is_active():
            log.error('ssh connection is not active')
            return

        cmd = command.encode(sys.stdout.encoding)
        stdin, stdout, stderr = self.client.exec_command(cmd, **kwargs)
        if stdin_param is not None:
            stdin.write(stdin_param)
            stdin.flush()

        stdout.channel.set_combine_stderr(combine_stderr)
        out = stdout.read().decode(sys.stdout.encoding)
        if out:
            log.info('%s stdout:\n%s' % (self.host, out.strip()))

        status_code = stdout.channel.recv_exit_status()
        if status_code != 0:
            err = stderr.read().decode(sys.stdout.encoding)
            if err:
                log.warn('%s stderr:\n%s' % (self.host, err.strip()))

        return status_code

    def sudo(self, command):
        cmd = 'sudo %s' % command
        return self.run(cmd, stdin_param=self.password, get_pty=True)


async def remote_run_async(host, command, credential=None,
                           stdout_queue=None, stderr_queue=None,
                           password=None, **kwargs):
    with RemoteHost(
        host, credential=credential,
        stdout_queue=stdout_queue, stderr_queue=stderr_queue
    ) as host:
        if credential is not None and credential.sudo:
            coroutine = host.sudo_async(command, password=password, **kwargs)
            status, stdout, stderr = await coroutine
        else:
            status, stdout, stderr = await host.run_async(command, **kwargs)
    return status, stdout, stderr


async def remote_batch_run(params, credential=None,
                           stdout_queue=None, stderr_queue=None,
                           password=None, **kwargs):
    tasks = []
    for host, command in params:
        run = remote_run_async(
            host, command, credential=credential,
            stdout_queue=stdout_queue, stderr_queue=stderr_queue,
            password=password, **kwargs
        )
        task = asyncio.ensure_future(run)
        tasks.append(task)
    results = await asyncio.gather(*tasks)
    return list(zip(results, params))

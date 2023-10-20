#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=
from typing import TYPE_CHECKING
from qnaplib.hero.main import HEROClient
from qnaplib.ts.main import TSClient
from baselib.linuxclient.main import LinuxClient
from baselib.robotlogger import RobotLogger
from baselib.robotkeyword import keyword
from baselib.mount import Mount
import qnaplib.errinj.nas_utils as NAS_UTILS

LOGGER = RobotLogger(__name__)

if TYPE_CHECKING:
    from qnaplib.errinj import ErrorInjection


class NAS:

    def __init__(self, errclient: "ErrorInjection",
                 ip_addr, username, password):
        # NAS product tag (auto detect)
        self.product = None

        # Define product and load corresponding client
        if ip_addr:
            self.product = self.define_product(ip_addr, username, password)
            if self.product == 'HERO':
                self.instance = HEROClient()
            elif self.product == 'TS':
                self.instance = TSClient()
            self.instance.connect(ip_addr, username, password)

        self.client = errclient
        self.load_utils()
        self.load_keywords()

    @property
    def attr(self):
        return self.instance

    @property
    def cli(self):
        return self.instance.cli

    @property
    def qcli(self):
        return self.instance.qcli

    @property
    def sftp(self):
        return self.instance.sftp

    @property
    def qpkg(self):
        return self.instance.qpkg

    @property
    def fltinj(self):
        return self.instance.fltinj

    @property
    def lux(self):
        return self.client.lux

    def define_product(self, ip_addr, username, password):
        client = LinuxClient(ip_addr, username, password)
        is_hero = client.run(
            '[ -f "/etc/QTS_ZFS" ] && echo "TRUE" || echo "FALSE"')
        product = 'HERO' if is_hero == 'TRUE' else 'TS'
        client.close()

        return product

    def load_utils(self):
        self.setup = NAS_UTILS.Setup(self)
        self.utils = NAS_UTILS.Utils(self)
        self.fio = NAS_UTILS.FIO(self)
        self.zfs = NAS_UTILS.ZFS(self)

    def load_keywords(self):
        self.client.add_sub_library_components(self, 'nas', [
            'setup', 'utils', 'fio', 'zfs'],
            manual_add_level=True)

    @keyword('NAS: CLI run')
    def run(self, cmd, run_async=False):
        '''
        Run CLI command on NAS
        - run_async == TRUE, the scripts won't wait for output and skip block
        '''
        if run_async:
            self.cli.run_async(cmd)
            return True
        return self.cli.run(cmd)

    @keyword('NAS: Mount server')
    def mount(self, server_ip=None, server_path=None, local_path=None,
              username=None, password=None, version='1.0'):
        '''
        Mount server on NAS
        - Use NFS mount by default
        - If username/password are provided, use CIFS mount
        - if server_ip not provide, Linux can still mount folder locally
        Arguments:
        | server_ip=<remote server IP>    | server_path=<remote server path>
        | local_path=<local folder path>          default=/mnt/evt_mount
        | username=<CIFS login username>          must provide for CIFS mount
        | password=<CIFS login password>          must provide for CIFS mount
        | version=<CIFS version>                  default=1.0
        '''
        return Mount(self).lux_mount(
            server_ip=server_ip, server_path=server_path,
            local_path=local_path, username=username,
            password=password, version=version)

    @keyword('NAS: Umount server')
    def umount(self, local_path):
        '''
        Umount remote server on NAS

        Arguments:
        | local_path=<local folder path>
        '''
        return Mount(self).lux_umount(local_path=local_path)

    @keyword('NAS: Copy files from NAS to Linux')
    def copy_files_from_nas_to_lux(self, nas_path, lux_path='/tmp/'):
        """
        Lib to copy files from NAS to VM
        :param nas_path: path of the files present in NAS
        :param lux_path: Path of the Linux where files shall be copied
        :return: Filepath of the Linux
        """
        LOGGER.info('|___Copying files from NAS___|')

        self.lux.cli.run(f'mkdir -p {lux_path}')
        filename = nas_path.split('/')[-1]
        filepath = f'{lux_path}/{filename}'
        self.sftp.copy_file_between_client(
            self, self.lux, nas_path, filepath)

        LOGGER.info(f'File is copied to VM [{filepath}]\n')
        return filepath

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=unused-argument, broad-except, too-many-lines
import time
import random
from typing import TYPE_CHECKING
from robot.libraries.BuiltIn import BuiltIn
from robot.running.context import EXECUTION_CONTEXTS
import tool.tool as tool
from baselib.robotlogger import RobotLogger
from baselib.robotkeyword import keyword
LOGGER = RobotLogger(__name__)

if TYPE_CHECKING:
    from .main import NAS


class Utils(object):

    def __init__(self, client: "NAS"):
        self.client = client

        # Check timeout
        self.check_timeout = 120
        # Check controller type
        self.ctrler_type = None
        self.ctrler_retry_count = None

    @property
    def cli(self):
        return self.client.cli

    @property
    def qcli(self):
        return self.client.qcli

    @property
    def fltinj(self):
        return self.client.fltinj

    @property
    def controller_type(self):
        if self.ctrler_type:
            LOGGER.debug(f'NAS controller type: {self.ctrler_type}\n')
            return self.ctrler_type

        cmd = 'lsmod | grep mpt3sas | head -n 1'
        ret = self.cli.run(cmd).split()
        if 'mpt3sas' in ret[0] and int(ret[-1]) > 0:
            self.ctrler_type = 'mpt3sas'
        else:
            self.ctrler_type = 'ata'

        LOGGER.debug(f'NAS controller type: {self.ctrler_type}\n')
        return self.ctrler_type

    @keyword('NAS: Utils: Save debug information')
    def save_debug_info(self):
        self.clear_dmesg_printing_output()
        self.cli.run('qcli_storage || true')
        self.cli.run('df -h  || true')

    @keyword('NAS: Utils: Clear dmesg and hide output')
    def clear_dmesg_ignore_output(self):
        '''
        Clear dmesg and hide all output
        - Use when tester want to clear dmesg but don't want to mess up report
        - Usually being called before test start
        '''
        LOGGER.info('|___Clear DMESG And Hide Output___|')
        cmd = 'dmesg -c > /dev/null 2>&1'
        self.cli.run(cmd)

        LOGGER.info('dmesg cleared!\n')
        return True

    @keyword('NAS: Utils: Clear dmesg and printing')
    def clear_dmesg_printing_output(self):
        '''
        Clear dmesg and ignore all output
        - Use when tester want to clear dmesg and log dmesg to report
        - Usually being called after test end
        '''
        LOGGER.info('|___Clear DMESG And Printing___|')

        cmd = 'dmesg -c'
        self.cli.run(cmd)

        LOGGER.info('dmesg cleared and printed to debug level!\n')
        return True

    @keyword('NAS: Utils: Check string show up in dmesg')
    def check_str_in_dmesg(self, checkstr, timeout=None):
        '''
        Check if specific string shows up in dmesg output
        - Usually being called after test to check if expected error shows up
        '''
        LOGGER.info(f'|___Check String {checkstr} Show Up In DMESG___|')

        timeout = timeout or self.check_timeout
        start_time = time.time()
        while True:
            if time.time() - start_time > int(timeout):
                full_output = self.cli.run('cat dmesglog')
                raise ValueError(f'Check string [{checkstr}] '
                                 f'not found in dmesg\n {full_output}')

            # Avoid cmd printing mess debug logs
            self.cli.run('dmesg > dmesglog')
            output = self.cli.run(f"grep '{checkstr}' dmesglog || true")
            if output:
                break

            LOGGER.info(f'{checkstr} is not in dmesg logs yet, '
                        f'pending retry...')
            time.sleep(2)

        LOGGER.info('String shows up in dmesg!\n')
        return True

    @keyword('NAS: Utils: Set watchdog threshold time')
    def set_watchdog_threshold(self, set_time):
        '''
        Set watchdog threshold time (default=10)
        - /proc/sys/kernel/watchdog_thresh
        '''
        LOGGER.info('|__Set Watchdog Threshold Time__|')
        cmd = f'echo {set_time} > /proc/sys/kernel/watchdog_thresh'
        LOGGER.info(f'CMD [{cmd}]')
        self.cli.run(cmd)

        LOGGER.info(f'Watchdog threshold time set\n')
        return True

    @keyword('NAS: Utils: Get file inode number')
    def get_file_inode(self, filepath):
        '''
        Get file inode number by stat command
        - filepath includes full path + filename
        '''
        LOGGER.info('|__Get File Inode Number__|')

        cmd = f"stat {filepath} | grep Inode | awk '{{print $4}}'"
        LOGGER.info(f'CMD [{cmd}]')

        start_time = time.time()
        while True:
            if time.time() - start_time > self.check_timeout:
                raise ValueError(
                    f'{filepath} inode cannot be fetched properly!')

            inode = self.cli.run(cmd)
            if inode.isdigit():
                break
            LOGGER.info(f'{filepath} inode does not have value yet, '
                        'pending retry ..')
            time.sleep(2)

        LOGGER.info(f'File [{filepath}] inode [{inode}]\n')
        return inode

    @keyword('NAS: Utils: Get pool major & minor number')
    def get_pool_major_minor_num(self, pool_id):
        '''
        Get pool major & minor number by qcli_storage & ls -li command
        - Return 3 values (major_num, minor_max_num, minor_min_num)
        '''
        LOGGER.info('|__Get Pool Major & Minor Number__|')
        LOGGER.info(f'Pool ID [{pool_id}]')
        storage_data = self.cli.run('qcli_storage').split('\n')
        pool_disks = [dk.split()[2] for dk in storage_data
                      if len(dk) > 0 and dk.split()[-2] == pool_id]
        LOGGER.info(f'Pool disks {pool_disks}')

        minor_nums = []
        for disk in pool_disks:
            disk_data = self.cli.run(f'ls -li {disk}')
            major_num = disk_data.split(',')[0].split()[-1]
            minor_nums.append(int(disk_data.split(',')[1].split()[0]))

        LOGGER.info(f'Pool major num [{major_num}]')
        min_minor_num, max_minor_num = min(minor_nums), max(minor_nums)
        LOGGER.info(f'Pool min minor num [{min_minor_num}]')
        LOGGER.info(f'Pool max minor num [{max_minor_num}]\n')

        return major_num, min_minor_num, max_minor_num

    @keyword('NAS: Utils: Drop caches')
    def drop_caches(self):
        '''
        Drop all pagecache, dentries and inodes caches on NAS client
        '''
        LOGGER.info('|___Drop Caches___|')

        cmd = f'sync && echo 3 | sudo tee /proc/sys/vm/drop_caches'
        self.cli.run(cmd)
        LOGGER.info(f'All caches dropped\n')

        return True

    @keyword('NAS: Utils: Create testfile')
    def create_testfile(self, path, filename='testfile'):
        '''
        Create testfile with random string for error injection testing
        '''
        LOGGER.info(f'|___Create {filename}___|')
        LOGGER.info(f'Path [{path}')

        randstr = tool.random_string(startwith='errinjtest_', length=10)
        filepath = f'{path}/{filename}'
        self.cli.run(f'sudo rm {filepath} || true')
        cmd = f'sudo echo "{randstr}" > {filepath}'
        LOGGER.info(f'CMD [{cmd}]')
        self.cli.run(cmd)

        LOGGER.info(f'{filename} created on [{filepath}]\n')
        return filepath

    @keyword('NAS: Utils: Read testfile')
    def read_testfile(self, filepath):
        '''
        Read testfile for error injection testing
        '''
        LOGGER.info('|___Read Testfile___|')

        LOGGER.info(f'File path [{filepath}]')

        cmd = f'sudo cat {filepath}'
        LOGGER.info(f'CMD [{cmd}]')
        self.cli.run(cmd)
        LOGGER.info(f'Testfile can be read properly\n')

        return True

    @keyword('NAS: Utils: Write testfile')
    def write_testfile(self, filepath):
        '''
        Write testfile for error injection testing
        '''
        LOGGER.info('|___Write Testfile___|')

        LOGGER.info(f'File path [{filepath}]')

        randstr = tool.random_string(startwith='writetest_', length=10)
        cmd = f'sudo echo "{randstr}" >> {filepath}'
        LOGGER.info(f'CMD [{cmd}]')
        self.cli.run(cmd)
        LOGGER.info(f'Testfile can be written properly\n')

        return True

    @keyword('NAS: Utils: Get pool equivalent decimal')
    def get_pool_decimal(self, pool_id):
        '''
        Convert poolID to equivalent decimal for error injection testing
        '''
        decimal = ord(str(pool_id))
        LOGGER.info(f'Convert poolID [{pool_id}] to ascii int [{decimal}]')
        return decimal

    @keyword('NAS: Utils: Check expected pool existence')
    def check_expected_pool(self, pool_id, expected_status='Error',
                            timeout=None):
        '''
        Check expected pool existence after error injection

        Arguments
        | pool_id: Pool id to validate pool status
        | timeout: Timeout to wait till pool reflects in expected state
        | expected_status: Expected status of the pool
        '''
        LOGGER.info(f'|___Check {expected_status} Pool Existence___|')

        LOGGER.info(f'Pool [{pool_id}]')

        timeout = timeout or self.check_timeout
        start_time = time.time()

        while True:
            # Section to handle timeout
            if time.time() - start_time > int(timeout):
                raise ValueError(f'Pool [{pool_id}] expected status '
                                 f'[{expected_status}] not show up!')

            # Section to judge pool status
            status = self.qcli.pool.info(
                action='get', section='table',
                column='Status', pool_id=pool_id)
            if status == expected_status:
                break

            # Section to log and sleep before next retry
            LOGGER.info(f'Pool {expected_status} not show up yet, '
                        'pending retry ..')
            time.sleep(5)

        LOGGER.info(f'Pool [{pool_id}] expected {expected_status} occurs!\n')
        return True

    def _get_storage_info(self):
        info = {}
        lines = self.cli.run('qcli_storage').split('\n')
        headers = lines[0].split()
        uidxs = [lines[0].find(head) for head in headers]
        for line in lines[1:]:
            if '/dev' not in line:
                continue  # Ignore abnormal data
            line_data = {}
            for idx, uidx in enumerate(uidxs):
                if idx+1 == len(uidxs):
                    line_data[headers[idx]] = line[uidx:].strip()
                else:
                    line_data[headers[idx]] = line[uidx:uidxs[idx+1]].strip()

                if headers[idx] == 'Pool':
                    # Remove (X) and (!) from pool for easy searching data
                    line_data[headers[idx]] = line_data[
                        headers[idx]].replace('(X)', '').replace('(!)', '')

            info[line_data['Port']] = line_data
        # Data structure
        # {'1':
        #   {
        #       'Enclosure': 'NAS_HOST',
        #       'Port': '1',
        #       'Sys_Name': '/dev/sda',
        #       'Size': '238.47 GB',
        #       'Type': 'data',
        #       'VDEV': 'vdev_1',
        #       'RAID_Type': 'RAID 0',
        #       'Group': '1',
        #       'Pool': '1',
        #       'SharedFolderName': 'Public'
        #   }, ...
        return info

    @keyword('NAS: Utils: Get pool raid disks')
    def get_pool_raid_disks(self, pool_id, spare=True):
        '''
        Get pool raid disks
        Arguments:
        | pool_id:    Pool id to fetch its raid disks
        | spare:      Boolean (True/False)
        |             If set to False return diskIDs excluding local spare

        Return:
        | diskIDs list (e.g. ['00000001', '00000002'])
        '''
        storage = self._get_storage_info()
        disk_ids = []
        for port, data in storage.items():
            # Find disks of pool
            if data['Pool'] == str(pool_id):
                dev = hex(int(port))[2:]
                disk_id = f'0000{(4 - len(dev)) * "0" + dev}'

                # Return disks if condition matches
                if spare or data['Type'] == 'data':
                    disk_ids.append(disk_id)

        return disk_ids

    @keyword('NAS: Utils: Get pool raid disks port id')
    def get_pool_raid_disks_port_id(self, pool_id, count='all', spare=True):
        '''
        Get pool raid disks port id

        Arguments
        | pool_id:    Pool id to fetch its port numbers
        | count:      Number of disk port numbers to fetch
        | spare:      Boolean (True/False)
        |             If set to False return port numbers excluding local spare

        Return:
        | port_nos in str format (e.g. '2' or '2,3' or '2,3,4')
        '''

        # Fetch list of disk ids from the pool
        disk_list = self.get_pool_raid_disks(pool_id, spare)

        # Choose specific number of disks from the disk list
        if count != 'all':
            disk_list = random.sample(disk_list, int(count))

        # Convert disk ids to port numbers and store in a list
        port_list = [str(int(disk[4:], 16)) for disk in disk_list]

        # Convert the list to string of port numbers
        port_nos = ','.join(map(str, port_list))

        return port_nos

    def _check_raid_disks_status(self, disk_ids, count='all',
                                 timeout=None, status='error'):
        '''
        Check specific status's raid disks existence after error injection

        Arguments
        | disk_ids:  Disk ids list
        | count:     all/any/n/0
        |            If count='all', then check all disks match status
        |            If count='any', then check one or more disks match status
        |            If count=n, then check n number of disks match status
        |            If count=0, then check for no disks match status
        | timeout:   set specific check timeout (default=120s)
        | status:    error/warning
        |            If status='error', then check if 'X' exist in diskname
        |            If status='warning', then check if '!' exist in diskname
        '''
        LOGGER.info('|___Check Specific Status\'s Raid Disks Existence___|')

        # Check if the status defined for checking
        support_statuses = {
            'error': 'X',
            'warning': '!'
        }
        if status.lower() not in support_statuses:
            raise ValueError(f'Invalid check status [{status}]! '
                             f'(Only support ({list(support_statuses)}')

        # Get the specific status for checking
        exp_status = support_statuses[status]
        status_str = status.lower()
        LOGGER.info(f'Raid disks {disk_ids}')
        LOGGER.info(f'  Check status [{status_str}]')
        LOGGER.info(f'  Expect [{count}] raid disks match the status')

        # Define waiting period (10s) for count=0 scenario
        # Each checking will minus 1 and pass the check if value == 0
        # To promise the error disks not showing up in the time period
        ensure_no_error_times = 5

        timeout = timeout or self.check_timeout
        start_time = time.time()

        while True:
            if time.time() - start_time > int(timeout):
                raise ValueError(f'Raid disks {disk_ids} expected {count} '
                                 f'{status_str} but the result mismatch!')

            match_disks = []
            storage = self._get_storage_info()
            for disk in disk_ids:
                port = str(int(disk[4:], 16))  # Convert diskID to Port
                if exp_status in storage[port]['Sys_Name']:
                    match_disks.append(disk)

            # Wait for any disks to match the status
            if count == 'any':
                if len(match_disks) > 0:
                    break
                LOGGER.info(f'No disks show {status_str}, pending '
                            f'[any] raid disks show {status_str} ..')

            # Wait for all disks to match the status
            elif count == 'all':
                if sorted(match_disks) == sorted(disk_ids):
                    break
                LOGGER.info(f'Current {status_str} disks {match_disks}, '
                            f'pending [all] raid disks show {status_str} ..')

            # Wait for specific number of disks to match the status
            elif int(count) > 0:
                if len(match_disks) == int(count):
                    break
                elif len(match_disks) > int(count):
                    raise ValueError(f'Expect only {count} {status_str} raid '
                                     f'disk but got {match_disks}!')
                LOGGER.info(f'Current {status_str} disks {match_disks}, '
                            f'pending {count} raid disks show {status_str} ..')

            # Wait for no raid disks to match the status
            else:
                if len(match_disks) == 0:
                    ensure_no_error_times -= 1
                    if ensure_no_error_times == 0:
                        break
                    else:
                        LOGGER.info(
                            f'Ensuring {status_str} not show up again ..')
                        time.sleep(2)
                        continue
                else:
                    LOGGER.info(
                        f'{match_disks} still show {status_str}, pending '
                        f'{count} raid disks show {status_str} ..')

            time.sleep(5)

        LOGGER.info(f'Expected {count} {status_str} disks show up!\n')
        return True

    @keyword('NAS: Utils: Check error raid disks existence')
    def check_error_raid_disks(self, disk_ids, count='all', timeout=None):
        '''
        Check error raid disks existence after error injection

        Arguments
        | disk_ids:  Disk ids list
        | count:     all/any/n/0
        |            If count='all', then check all disks show error
        |            If count='any', then check one or more disks show error
        |            If count=n, then check n number of disks show error
        |            If count=0, then check for no error disks
        | timeout:   set specific check timeout (default=120s)
        '''
        return self._check_raid_disks_status(
            disk_ids=disk_ids, count=count, timeout=timeout, status='error')

    @keyword('NAS: Utils: Check warning raid disks existence')
    def check_warning_raid_disks(self, disk_ids, count='all', timeout=None):
        '''
        Check warning raid disks existence after error injection

        Arguments
        | disk_ids:  Disk ids list
        | count:     all/any/n/0
        |            If count='all', then check all disks show warning
        |            If count='any', then check one or more disks show warning
        |            If count=n, then check n number of disks show warning
        |            If count=0, then check for no warning disks
        | timeout:   set specific check timeout (default=120s)
        '''
        return self._check_raid_disks_status(
            disk_ids=disk_ids, count=count, timeout=timeout, status='warning')

    @keyword('NAS: Utils: Recover raid disks error')
    def recover_raid_disks_error(self, timeout=None):
        '''
        Recover all disks error after error injection
        - Using hal_event --pd_clear_error dev_id=0x.. to recover disk error
        '''
        LOGGER.info('|___Recover Raid Disks Error___|')

        storage = self._get_storage_info()
        for port, data in storage.items():
            if 'X' in data['Sys_Name']:
                dev = hex(int(port))
                LOGGER.info(f'Recovering disk port {port} - {dev}')
                self.cli.run(f'hal_event --pd_clear_error dev_id={dev}')

        timeout = timeout or self.check_timeout
        start_time = time.time()
        retry_flag = True

        while True:
            if time.time() - start_time > timeout:
                if retry_flag:
                    # Recover disks using plug-out, plug-in
                    # In case not recovered using hal-event
                    LOGGER.info('Disks not recovered using hal_event, '
                                'retrying using plug-out, plug-in disks..')
                    storage = self._get_storage_info()

                    for data in storage.values():
                        if 'X' in data['Sys_Name']:
                            self.plug_out_disk(port_id=data['Port'])
                            self.plug_in_disk()

                    retry_flag = False
                    timeout += timeout
                else:
                    raise ValueError(f'Raid disks error not recover!')

            error_disks = []
            storage = self._get_storage_info()
            for data in storage.values():
                if 'X' in data['Sys_Name']:
                    dev = hex(int(data['Port']))[2:]
                    error_disks.append(f'0000{(4 - len(dev)) * "0" + dev}')

            if not error_disks:
                break
            LOGGER.info(f'{error_disks} still show error, pending retry ..')
            time.sleep(5)

        LOGGER.info(f'All disks recovered!\n')
        return True

    @keyword('NAS: Utils: Run keyword but expect error')
    def run_keyword_expect_error(self, func, *args, **kwargs):
        '''
        Run a keyword on NAS but expect error for error injection testing

        Arguments
        | func=<python func or robot keyword>
        | *args, **kwargs=positional or keyword arguments of above func
        '''
        LOGGER.info('|___Run Keyword But Expect Error___|')

        error_occur = False
        origin_limit = self.cli.set_try_limit(0)
        LOGGER.redirect_error_to_info = True
        LOGGER.lock = True

        # Check if func is robot keyword
        if isinstance(func, str):
            if EXECUTION_CONTEXTS.current is None:
                raise ValueError('func is str() but robot process not exist!')

            # Converting robot keyword into python func
            args = [func, *args]
            for key, val in kwargs.items():
                args.append(f'{key}={val}')
            kwargs = {}
            func = BuiltIn().run_keyword

        # Start running func
        try:
            func(*args, **kwargs)
        except Exception:
            error_occur = True
        finally:
            self.cli.set_try_limit(origin_limit)
            LOGGER.lock = False
            LOGGER.redirect_error_to_info = False

        if not error_occur:
            raise ValueError('Keyword expected error but nothing occur!')

        LOGGER.info('Keyword expected error occurs!\n')
        return True

    @keyword('NAS: Utils: Plug-out disk')
    def plug_out_disk(self, port_id=None, count=1, disktype='hdd', free=True):
        '''
        This library will unplug drives using port id's

        Arguments
        | port_id:    Port id should be in str format (e.g: '5', '5,6')
        | count:      Number of disks to be unplugged (e.g: 1,2 or all)
        '''
        LOGGER.info(f'|___Unplugging port {port_id} disk___|')

        self.fltinj.disk.pick_disk(port_id, count, disktype, free)
        self.fltinj.disk.plug_out()

        LOGGER.info('Unplugged the disks successfully!\n')
        return True

    @keyword('NAS: Utils: Plug-in disk')
    def plug_in_disk(self):
        '''
        This library will restore unplugged drives
        '''
        LOGGER.info('|___Restoring unplugged disks___|')

        self.fltinj.disk.restore_all()
        self.fltinj.disk.clear_picked_disk()

        LOGGER.info('Restored the disks successfully!\n')
        return True

    @keyword('NAS: Utils: Define controller retry count')
    def define_ctrler_retry_count(self, ata_retry_count, mpt3sas_retry_count):
        '''
        Lib to define retry count based on controller type

        Arguments:
        | ata_retry_count: retry count for ata controller
        | mpt3sas_retry_count: retry count for mpt3sas controller
        '''
        LOGGER.info('|___Define Controller Retry Count___|')
        controller = self.controller_type
        if controller == 'ata':
            self.ctrler_retry_count = int(ata_retry_count)
        else:
            self.ctrler_retry_count = int(mpt3sas_retry_count)

        LOGGER.info(f'NAS controller type: {self.ctrler_type}\n')
        LOGGER.info(
            f'Define controller retry count: {self.ctrler_retry_count}\n')
        return True

    @keyword('NAS: Utils: Get controller retry count')
    def get_ctrler_retry_count(self):
        '''
        Lib to return retry count
        - Use "define_ctrler_retry_count" to define ctrler_retry_count prior
          to use this keyword
        '''
        LOGGER.info('|___Get Controller Retry Count___|')

        if self.ctrler_retry_count is None:
            raise ValueError("ctrler_retry_count is not defined"
                             "Use lib define_ctrler_retry_count first!\n")
        LOGGER.info(f'Controller retry count: {self.ctrler_retry_count}\n')
        return self.ctrler_retry_count

    @keyword('NAS: Utils: Get mount path')
    def get_mount_path(self, vol):
        '''
        Lib to get the mounted path of the volume/lun

        Arguments:
            | vol=<zfs vol name>         e.g. vol='/dev/sdwa'
        '''
        LOGGER.info(f'|___Get Mounted Path of {vol}___|')

        cmd = 'mount'
        out = self.cli.run(cmd)

        mount_path = ''
        for line in out.splitlines():
            if vol in line:
                mount_path = line.split()[2]
                break

        LOGGER.info(f'Mounted path of {vol}: {mount_path}\n')
        return mount_path

    @keyword('NAS: Utils: Perform dd write')
    def perform_dd_write(self, outputfile, inputfile='/dev/urandom',
                         blocksize='1M', count='1000', seek=None):
        '''
        Lib to perform dd write for error injection testing

        Arguments:
        | outputfile: Output file where write to be performed
        | inputfile: Input file for dd write
        | blocksize: Block size for write
        | count: count for write
        | seek: Option to write from the specific location
        '''
        LOGGER.info('|___Perform DD write___|')

        cmd = f'dd if={inputfile} of={outputfile} bs={blocksize} count={count}'
        if seek is not None:
            cmd = f'{cmd} seek={seek}'
        self.cli.run(cmd)

        LOGGER.info('DD write performed successfully\n')
        return True

    @keyword('NAS: Utils: Get lun blocksize')
    def get_lun_blocksize(self, lun_id):
        '''
        Lib to get blocksize of lun

        Arguments:
        | lun_id: Lun id to get the blocksize
        '''
        LOGGER.info('|___Get LUN Blocksize___|')

        raw_block_size = self.client.setup.get_lun_info(
            lun_id, action='get', section='table', column='BlockSize')
        block_size = tool.conv_to_basesize(raw_block_size)

        LOGGER.info(f'Blocksize of LUN: {block_size}\n')
        return block_size

    @keyword('NAS: Utils: Get md5sum')
    def get_md5sum(self, filename):
        '''
        Lib to get md5sum value for file

        Arguments:
        | filename: file name to get the md5sum
        '''
        LOGGER.info(f'|___Get md5sum for {filename}___|')

        cmd = f'md5sum {filename}'
        md5sum = self.cli.run(cmd).split()[0]

        LOGGER.info(f'md5sum value: {md5sum}\n')
        return md5sum

    @keyword('NAS: Utils: Convert to hexadecimal')
    def convert_to_hexadecimal(self, value):
        '''
        Lib to convert value to hexadecimal

        Arguments:
        | value: Value to be converted to hexadecimal
        '''
        LOGGER.info(f'|___Convert {value} to Hexadecimal___|')

        hex_value = hex(int(value)).lstrip("0x")

        LOGGER.info(f'Hexadecimal value of {value}: {hex_value}\n')
        return hex_value

    @keyword('NAS: Utils: Get username by UUID')
    def get_username_by_uuid(self, uuid):
        '''
        Lib to get username based on UUID

        Arguments
        | uuid: uuid of the user in the NAS
        '''
        LOGGER.info(f'|___Get Username by UUID {uuid}___|')

        cmd = f'cat /etc/passwd'
        out = self.cli.run(cmd)

        username = None
        for line in out.strip().splitlines():
            if uuid in line:
                username = line.split(":")[0]
                LOGGER.info(f'Username for UUID {uuid}: {username}\n')
                break

        if not username:
            raise ValueError(f'Username from UUID {uuid} not found!')

        return username

    @keyword('NAS: Utils: Get UUID by username')
    def get_uuid_by_username(self, username):
        '''
        Lib to get the user/uuid of the NAS user

        Arguments
        | username: User added in NAS
        '''
        LOGGER.info(f'|___Get UUID by Username {username}___|')

        cmd = f'cat /etc/passwd'
        out = self.cli.run(cmd)

        if username not in out:
            raise ValueError(f'Did not find {username} in {out}')

        uuid = None
        for line in out.strip().splitlines():
            if username in line:
                uuid = line.split(":")[2]
                LOGGER.info(f'UUID of {username}: {uuid}\n')
                break

        if not uuid:
            raise ValueError(f'UUID for username {username} not found!')

        return uuid

    @keyword('NAS: Utils: Update UUID mount in file')
    def update_uuid_mount_in_cfile(self, cfile, nuuid, nmpath, nfile='tmp.c'):
        '''
        Lib to update UUID and Mount in .C file

        Arguments:
        | cfile: .c file from stap
        | nuuid: NAS user uuid
        | nmpath: NAS mount path
        | nfile: NAS temporary file used to update the contents of .c file
        '''
        LOGGER.info(f'|___Update UUID and Mount Path in .C___|')

        cmd = f'cat /dev/null > {nfile}'
        self.cli.run(cmd)
        cmd = f'cat {cfile}'
        out = self.cli.run(cmd)

        # Update UUID and Mount path
        split_out = out.strip().splitlines()
        for line in split_out:
            if 'nfs4_setfacl' in line:
                old_uuid = line.split()[-2].split(":")[2]
                old_mount = line.split('"')[1].split()[-1]
                LOGGER.debug(f'Old UUID: {old_uuid}, mount: {old_mount}\n'
                             f'Updating to UUID: {nuuid}, mount: {nmpath}')
                out = out.replace(old_uuid, nuuid)
                out = out.replace(old_mount, nmpath)
        LOGGER.debug(f'Updated contents: {out}\n')

        # Copy updated contents to .c file
        for line in out.splitlines():
            cmd = f"echo '{line}' >> {nfile}"
            self.cli.run(cmd)
        cmd = f'cp {nfile} {cfile}'
        self.cli.run(cmd)

        LOGGER.info(f'Contents updated successfully..\n')
        return True

    @keyword('NAS: Utils: Update permissions in NAS path')
    def update_permissions_in_nas(self, permissions, naspath):
        '''
        Lib to update NAS path permissions

        Arguments:
        | permissions: permissions to be given to file
        | naspath: path to update permissions
        '''
        LOGGER.info(f'|___Set {permissions} for {naspath}___|')

        cmd = f'chmod {permissions} {naspath}'
        self.cli.run(cmd)

        LOGGER.info('Permissions Updated\n')
        return True

    @keyword('NAS: Utils: Set NFS ACL')
    def set_nfs_acl(self, client_user=None, client_uuid=None,
                    client_mpath=None, acl_attr=None):
        '''
        Lib to set NFS ACL

        Arguments:
        | client_user: User created in Client NAS
        | client_uuid: UUid of the user of client NAS
        | client_mpath: Mount path of the client NAS
        | acl_attr: ACL attribute
        '''
        LOGGER.info(f'|___Set NFS ACL___|')

        if client_user:
            cmd = f'sudo -u {client_user} nfs4_setfacl -a ' \
                  f'A:fd:{client_uuid}:{acl_attr} {client_mpath}'
        else:
            cmd = f'nfs4_setfacl -a D:fd:{client_uuid}:{acl_attr} ' \
                  f'{client_mpath}'
        self.cli.run(cmd)

        LOGGER.info('NFS ACL set\n')
        return True

    @keyword('NAS: Utils: Get NFS ACL')
    def get_nfs_acl(self, file1_path, file2_path):
        '''
        Lib to execute get NFS ACL command

        Arguments:
        | file1_path: Path of file 1 created in client mount path
        | file2_path: Path of file 2 created in client mount path
        '''
        LOGGER.info('|___Get NFS ACL___|')

        cmd = f'nfs4_getfacl {file1_path} | nfs4_setfacl -S - {file2_path}'
        self.cli.run(cmd)

        LOGGER.info('Get NFS ACL executed successfully\n')
        return True

    @keyword('NAS: Utils: Execute modified binary')
    def execute_modified_binary(
            self, path, modified_binary, file, args='', validate_locked=False,
            tmp_filepath=False):
        '''
        Lib to execute binary files

        Arguments
        | path: Path where compiled file is copied on NAS
        | modified_binary: File to be executed
        | file: file name with path of the file  eg: </mnt/my_nas_share/file1>
        | args: Other arguments required for compiled file to run
        | validate_locked: Flag to be set True, if validation for
        |                  Already Locked Process string is required
        | tmp_filepath: Boolean <True/False>  Set to True if temporary file
        |                                 is required
        '''
        LOGGER.info('|___Execute Modified Binary___|')

        # Change permissions of compiled file
        self.cli.run(f'chmod +x {path}/{modified_binary}')

        # Create temp file if required
        cmd = f'cd {path} && ./{modified_binary} '
        if tmp_filepath:
            tmp_filepath = '/tmp/file.txt'
            self.cli.run(f'cat /dev/null > {tmp_filepath}')
            cmd += f'{tmp_filepath} '

        # Add arguments & execute modified_binary
        cmd += f'{file} {args}'
        LOGGER.debug(f'Command to execute compile file: {cmd}')
        ret = self.cli.run(cmd)

        # Validate process locked based on requirement
        if validate_locked and 'Already locked by another process' not in ret:
            raise ValueError(f'Expected Already locked string but got {ret}\n')

        LOGGER.info('Executed modified binary..\n')
        return True

    @keyword('NAS: Utils: Create testdir')
    def create_testdir(self, path, dirname='testdir'):
        '''
        Lib to create test dir for error injection

        Arguments:
        | path: Path where directory to be created
        | dirname: Name of the directory to be created
        '''
        LOGGER.info(f'|___Create {dirname}___|')

        dirpath = f'{path}/{dirname}'
        self.cli.run(f'sudo rm -rf {dirpath} || true')
        self.cli.run(f'sudo mkdir -p {dirpath}')

        LOGGER.info(f'{dirname} created at {path}\n')
        return dirpath

    @keyword('NAS: Utils: Check and update disk volume conf')
    def check_update_disk_volume_conf(self, disk_id, timeout=None):
        '''
        Check and update disk's volume configurations

        Usage of storage_util --volume_scan
        | storage_util --volume_scan do_scan_raid=1 force=1 command scans for
        | any changes to the disk configuration, missing disk volume config
        | and updates the RAID information accordingly.
        | This includes checking for newly added disks, disk failures, and
        | changes to disk signatures.


        Arguments
        | disk_id: diskID of the disk whose volume config needs to be checked
        |          and updated
        '''
        LOGGER.info(f'|___Check DISK: 0x{disk_id} info in volume conf___|')

        timeout = timeout or self.check_timeout
        start_time = time.time()
        while True:
            if time.time() - start_time > int(timeout):
                raise ValueError(f'DISK: 0x{disk_id} has no volume config!')

            cmd = 'cat /etc/volume.conf | grep diskId'
            out = self.cli.run(cmd)

            # Check diskID available in volume conf file
            if any(f'0x{disk_id}' in line.split('=')[-1] for line in
                   out.strip().splitlines()):
                break

            # Run storage_util command to get disk info updated in volume conf
            self.cli.run('storage_util --volume_scan do_scan_raid=1 force=1')
            LOGGER.info(f'Disk: 0x{disk_id} not found in volume conf yet,'
                        f'pending retry...')
            time.sleep(2)

        LOGGER.info(f'DISK: 0x{disk_id} info shows up in volume conf file!\n')

    @keyword('NAS: Utils: Enable RPC debug flag')
    def enable_rpcdebug_flag(self):
        '''
        Lib to enable RPC debug flag
        '''
        LOGGER.info('|___Enable RPC debug flag___|')

        self.cli.run('rpcdebug -m nfs -s all')
        self.cli.run('rpcdebug -m rpc -s all')

        LOGGER.info('RPC debug flag enabled\n')
        return True

    @keyword('NAS: Utils: Disable RPC debug flag')
    def disable_rpcdebug_flag(self):
        '''
        Lib to disable RPC debug flag
        '''
        LOGGER.info('|___Disable RPC debug flag___|')

        self.cli.run('rpcdebug -m nfs -c all')
        self.cli.run('rpcdebug -m rpc -c all')

        LOGGER.info('RPC debug flag disabled\n')
        return True

    @keyword('NAS: Utils: Execute compile file')
    def execute_compile_file(self, path, compiled_file, file, args='',
                             validate_locked=False):
        '''
        Lib to execute compiled .c files

        Arguments:
        | path: Path where compiled file is copied on NAS
        | compiled_file: File to be executed
        | file: file name with path of the file  eg: </mnt/my_nas_share/file1>
        | args: Other arguments required for compiled file to run
        | validate_locked: Flag to be set True, if validation for
        |                  Already Locked Process string is required
        '''
        LOGGER.info('|___Execute Compiled File___|')

        cmd = f'cd {path} && ./{compiled_file} {file} {args}'
        ret = self.cli.run(cmd)

        if validate_locked is True:
            if 'Already locked by another process' not in ret:
                raise ValueError(f'Expected Already locked string '
                                 f'but got {ret}\n')

        LOGGER.info('Executed compiled file..\n')
        return True

    @keyword('NAS: Utils: Remove testfile')
    def remove_testfile(self, filepath):
        '''
        Lib to remove file from path for error injection

        Arguments:
        | filepath: path of file to be removed
        '''
        LOGGER.info(f'|___Remove file from {filepath}___|')

        self.cli.run(f'rm {filepath}')

        LOGGER.info(f'File removed from {filepath}\n')
        return True

    @keyword('NAS: Utils: Remove testdir')
    def remove_testdir(self, dirpath):
        '''
        Lib to remove testdir for error injection

        Arguments:
        | dirpath: path of directory to be removed
        '''
        LOGGER.info(f'|___Remove dir from {dirpath}___|')

        self.cli.run(f'rm -rf {dirpath}')

        LOGGER.info(f'Directory removed from {dirpath}\n')
        return True

    @keyword('NAS: Utils: Get file size')
    def get_file_size(self, filepath, base_size='Byte'):
        '''
        Lib to get file size

        Arguments:
        | filepath: Path of the file to get the file size
        '''
        LOGGER.info(f'|___Get File Size of {filepath}___|')

        cmd = f"stat {filepath} | grep Size | awk '{{print $2}}'"
        LOGGER.info(f'CMD [{cmd}]')

        start_time = time.time()
        while True:
            if time.time() - start_time > self.check_timeout:
                raise ValueError(
                    f'{filepath} size cannot be fetched properly!')

            size = self.cli.run(cmd)
            if size.isdigit():
                break
            LOGGER.info(f'{filepath} size does not have value yet, '
                        'pending retry ..')
            time.sleep(2)

        LOGGER.info(f'File size retrieved: {size},\n '
                    f'converting to base size: {base_size}\n')
        size = tool.conv_to_basesize(size, input_base=base_size)

        LOGGER.info(f'File [{filepath}] size [{size}]\n')
        return size

    @keyword('NAS: Utils: Check cache status')
    def check_cache_status(self, cache_id, timeout=None,
                           expected_status='Error'):
        '''
        Check expected cache pool existence after error injection

        Arguments:
        | cache_id: Cache pool id
        | timeout: wait time to reflect pool in expected state
        | expected_status: Expected status of cache pool
        '''
        LOGGER.info(f'|___Check {expected_status} Cache Pool Existence___|')

        timeout = timeout or self.check_timeout
        start_time = time.time()

        while True:
            if time.time() - start_time > timeout:
                raise ValueError('Cache pool [{cache_id}] expected '
                                 f'{expected_status} but nothing occur!')

            status = self.client.setup.get_cache_info(
                action='get', section='table', column='Status',
                pool_id=cache_id)
            if status == expected_status:
                break

            LOGGER.info(f'Pool {expected_status} not show up yet, '
                        'pending retry ..')
            time.sleep(5)

        LOGGER.info(f'Cache [{cache_id}] expected {expected_status} occurs!\n')
        return True

    @keyword('NAS: Utils: Get disk sys name')
    def get_disk_sys_name(self, disk_list):
        '''
        Lib to get corresponding disk sys name for the provided disk ids

        Arguments
        | disk_List: list of disk ids (e.g: ['00000006','0000000a']

        - Returns a list of disk sys name
        '''
        sys_name = []
        storage = self._get_storage_info()
        for disk in disk_list:
            port = str(int(disk[4:], 16))  # Convert diskID to Port
            sys_name.append(storage[port]['Sys_Name'])

        return sys_name

    @keyword('NAS: Utils: Get system ODX value')
    def get_system_odx_value(self, odx_flag):
        '''
        Lib to get the system odx value for Windows VM testing

        Arguments
        | odx_flag: odx flag for which value to be retrieved
        | <odx_acc_enable | odx_acc_fail | odx_acc_success |
        |  odx_start_unaligned | odx_blocksize_mismatch>
        '''
        LOGGER.info('|___Get ODX Value___|')

        ret = self.cli.run('sysctl -a | grep odx')
        value = ''
        for line in ret.splitlines():
            if odx_flag in line:
                value = line.split()[-1]
                break

        if not value:
            raise ValueError(f'Not able to retrieve {odx_flag}')

        LOGGER.info(f'Value retrieved for {odx_flag}: {value}\n')
        return value

    @keyword('NAS: Utils: Move testfile')
    def move_testfile(self, old_path, new_path):
        '''
        Lib to rename file from path for error injection

        Arguments
        | old_path: Current path of the file
        | new_path: New path of the file to be moved to
        '''
        LOGGER.info(f'|___Move {old_path} to {new_path}___|')
        cmd = f'mv {old_path} {new_path}'
        self.cli.run(cmd)
        LOGGER.info(f'Successfully moved {old_path} to {new_path}!\n')
        return True

    @keyword('NAS: Utils: Create empty file')
    def create_empty_file(self, file_path):
        '''
        Lib to create empty file using touch command

        Arguments
        | file_path: Absolute path of the file to be created
        '''
        LOGGER.info(f'|___Create empty file using touch command___|')

        cmd = f'touch {file_path}'
        LOGGER.info(f'CMD [{cmd}]')
        self.cli.run(cmd)

        LOGGER.info(f'Empty file created at the path: {file_path}\n')
        return file_path

    @keyword('NAS: Utils: Get smart attributes')
    def get_smart_attributes(self, att_name, port):
        '''
        Lib to get smart attributes on HERO NAS
        '''
        cmd = f'cat /tmp/smart/smart_0_{port}.info'
        out = self.cli.run(cmd)
        smart_attributes = ''
        for line in out.splitlines():
            if att_name in line:
                smart_attributes = line.split(",")
                break

        smartid = smart_attributes[0]
        threshold = int(smart_attributes[2])
        start_threshold = threshold + 50
        duration = 150
        decrement_value = 5
        exit_value = threshold
        option = 1
        values = (smartid, start_threshold, duration, decrement_value,
                  exit_value, option)

        return values

    @keyword('NAS: Utils: Set debug level flag')
    def set_debug_level_flag(self):
        '''
        Set Debug level flag
        '''
        LOGGER.info('|___Set Debug Level Flag___|')

        cmd = 'echo 6 >> /proc/sys/kern/scst/debug_level'
        self.cli.run(cmd)

        LOGGER.info('Debug level flag is set\n')
        return True

    @keyword('NAS: Utils: Disable debug level flag')
    def disable_debug_level_flag(self):
        '''
        Disable Debug level flag
        '''
        LOGGER.info('|___Disable debug level flag___|')

        cmd = 'echo 2 >> /proc/sys/kern/scst/debug_level'
        self.cli.run(cmd)

        LOGGER.info('Debug level flag disabled\n')
        return True

    @keyword('NAS: Utils: Set NFS grace time')
    def set_nfs_grace_time(self, set_time):
        '''
        Lib to update NFS grace time for NFS enabled sharedfolder

        Arguments
        | set_time: Grace time to be set (in sec)
        '''
        LOGGER.info(f'|___Set NFS grace time to {set_time}___|')

        # Update grace time
        cmd = f"sed -i 's/rpc\\.nfsd \\$NO_V3 \\$NO_V4/rpc.nfsd -G " \
              f"{set_time} \\$NO_V3 \\$NO_V4/g' /etc/init.d/nfs"
        self.cli.run(cmd)

        # Restart NFS services
        self.cli.run('/etc/init.d/nfs stop')
        self.cli.run('/etc/init.d/nfs start')
        grace_time = self.cli.run('cat /proc/fs/nfsd/nfsv4gracetime')

        if int(grace_time) != int(set_time):
            raise ValueError(f'Grace time not updated..'
                             f'Grace time expected value: {set_time}'
                             f'Grace time actual value: {grace_time}')

        LOGGER.info('Updated grace time!!\n')
        return True

    @keyword('NAS: Utils: Check snapsync jobs expected state')
    def check_jobs_expected_state(self, expected_state, timeout=None):
        '''
        Lib to check snapsync jobs to expected state

        Arguments
        | expected_state: Expected state of snapsync jobs
        | timeout: Wait time for the jobs to reach expected state
        '''
        LOGGER.info('|___Check snapsync jobs expected state___|')

        timeout = timeout or self.check_timeout
        start_time = time.time()
        uids = self.qcli.snapsync.job_list(
            action='get', section='table', column='uids')

        for job_id in uids:
            while True:
                if time.time() - start_time > timeout:
                    raise ValueError('Expected state for snapsync jobs not '
                                     f'found for job {job_id}')

                state = self.qcli.snapsync.job_list(
                    action='get', section='table', column='State',
                    job_id=job_id)
                if state == expected_state:
                    break

                LOGGER.info('Snapsync job expected state not retrieved, '
                            'pending retry..')
                time.sleep(5)

        LOGGER.info('Snapsync jobs expected state retrieved\n')
        return True

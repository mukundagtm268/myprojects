#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=unused-argument, broad-except
import time
from typing import TYPE_CHECKING
from baselib.robotlogger import RobotLogger
from baselib.robotkeyword import keyword
import tool.tool
LOGGER = RobotLogger(__name__)

if TYPE_CHECKING:
    from .main import NAS


class ZFS(object):

    def __init__(self, client: "NAS"):
        self.client = client

        # Check timeout
        self.check_timeout = 120

    @property
    def cli(self):
        return self.client.cli

    @keyword('NAS: Utils: Enable ZFS debug flag')
    def enable_zfs_debug_flag(self):
        '''
        Enable ZFS debug flag
        - /sys/module/zfs/parameters/_vfs_zfs_zibread_dbglevel
        '''
        return self._set_zfs_debug_flag(enable=True)

    @keyword('NAS: Utils: Disable ZFS debug flag')
    def disable_zfs_debug_flag(self):
        '''
        Disable ZFS debug flag
        - /sys/module/zfs/parameters/_vfs_zfs_zibread_dbglevel
        '''
        return self._set_zfs_debug_flag(enable=False)

    def _set_zfs_debug_flag(self, enable=False):
        LOGGER.info('|__Set ZFS Debug Flag__|')
        opt = 1 if enable is True else 0
        cmd = (f'echo {opt} > '
               '/sys/module/zfs/parameters/_vfs_zfs_zibread_dbglevel')
        LOGGER.info(f'CMD [{cmd}]')
        self.cli.run(cmd)

        LOGGER.info(f'ZFS debug flag set\n')
        return True

    @keyword('NAS: Utils: Get ZFS pool dataset id')
    def get_zfs_pool_dataset_id(self, pool_id, data_id=False, snap_id=False):
        '''
        Fetching ZFS pool corresponding dataset ID for error injection
        - This function is only for HERO NAS
        Arguments:
        | pool_id: pool ID for which dataset paths required
        | data_id: Boolean (True/False),
        |          shall return data id only if set True
        | snap_id: Boolean (True/False),
        |          shall return snap id only if set True
        '''
        LOGGER.info(f'Fetching ZFS pool [{pool_id}] dataset id ..')
        cmd = (f"zdb -d zpool{pool_id} | grep -n ZVOL "
               "| grep -v init | awk '{print $5}'")
        output = self.cli.run(cmd).strip()
        if not output:
            cmd = (f"zdb -d zpool{pool_id} | grep -n ZPL "
                   "| grep -v init | awk '{print $5}'")
            output = self.cli.run(cmd).strip()

        dataset_id = output.replace(',', '')
        split_data_id = dataset_id.split()
        if data_id:
            return split_data_id[-1]
        elif snap_id:
            return split_data_id[0]

        LOGGER.info(f'Dataset id [{dataset_id}]\n')
        return dataset_id

    @keyword('NAS: Utils: Scrub zpool')
    def zpool_scrub(self, zpool_name):
        '''
        Scrub the given pool
        - This function is only for HERO NAS

        Arguments
        | zpool_name:   zpool name (e.g: zpool2, zpool3)
        '''
        LOGGER.info(f'|___Scrub [{zpool_name}]___|')

        cmd = f'zpool scrub {zpool_name}'
        self.cli.run(cmd)

        LOGGER.info(f'Scrubbed {zpool_name} successfully!\n')
        return True

    @keyword('NAS: Utils: Check zpool status')
    def check_zpool_status(self, zpool_name, check_key='state',
                           expected_value=None, timeout=None):
        '''
        Check zpool status
        - This function is only for HERO NAS

        Arguments
        | zpool_name:     zpool name (e.g: zpool2, zpool3)
        | check_key:      Key whose value need to checked (e.g: state/scan)
        | expected_value: Expected value of the given key
        |                 case1:check_key=state, expected_value=ONLINE/DEGRADED
        |                 case2:check_key=scan, expected_value=scrub repaired/
        |                       scrub in progress/ none requested
        '''
        LOGGER.info(f'|___Get expected {zpool_name} status___|')

        got_value = ''
        timeout = timeout or self.check_timeout
        start_time = time.time()

        # Wait for expected zpool status
        while True:
            if time.time() - start_time > int(timeout):
                raise ValueError(f'{zpool_name} expected {check_key} '
                                 f'to show {expected_value} '
                                 f'but nothing occur!')

            # Fetch the zpool status info.
            out = self.cli.run(f'zpool status {zpool_name}')
            for line in out.splitlines():
                # Extract the expected value for the provided key
                if line.split(':')[0].strip() == check_key:
                    got_value = line.split(':')[1].strip()
                    break

            # Check if expected value occurs ignoring the case
            if expected_value.lower() in got_value.lower():
                break

            LOGGER.info(f'{zpool_name} expected {check_key} '
                        f'value not show up yet, pending retry ..')
            time.sleep(5)

        LOGGER.info(f'{zpool_name} expected {check_key} '
                    f'{expected_value} occurs!\n')
        return True

    @keyword('NAS: Utils: Get ZFS pool dataset path')
    def get_zfs_pool_dataset_path(self, pool_id, data_path=False,
                                  snap_path=False):
        '''
        Fetching ZFS pool corresponding dataset path for error injection
        - This function is only for HERO NAS
        Arguments:
        | pool_id: pool ID for which dataset paths required
        | data_path: Boolean (True/False),
        |            shall return data path only if set True
        | snap_path: Boolean (True/False),
        |            shall return snap path only if set True
        '''
        LOGGER.info(f'Fetching ZFS pool [{pool_id}] dataset path')

        cmd = (f"zdb -d zpool{pool_id} | grep -n ZVOL "
               "| grep -v init | awk '{print $2}'")
        path = self.cli.run(cmd).strip()
        if not path:
            cmd = (f"zdb -d zpool{pool_id} | grep -n ZPL "
                   "| grep -v init | awk '{print $2}'")
            path = self.cli.run(cmd).strip()

        split_path = path.split()
        if data_path:
            return split_path[-1]
        elif snap_path:
            return split_path[0]

        LOGGER.info(f'Dataset path [{path}]\n')
        return path

    @keyword('NAS: Utils: Flush ZFS ARC caches')
    def flush_zfs_arc_caches(self):
        '''
        Flush ZFS ARC caches by zinject
        - This function is only for HERO NAS
        '''
        LOGGER.info(f'Flushing ZFS ARC caches ..')
        self.cli.run('zinject -a')

        LOGGER.info(f'ZFS ARC caches flushed\n')
        return True

    @keyword('NAS: Utils: Get ZFS folder path')
    def get_folder_path(self, folder):
        '''
        Library to get the complete sharedfolder (Volume) path using zfs list
        - This function is only for HERO NAS
        '''
        LOGGER.info('|___Get ZFS Shared Folder Path___|')

        vol_path = ''
        out = self.cli.run('zfs list')

        target_folder = f'{folder}/@Recently-Snapshot'
        for line in out.splitlines():
            if target_folder in line:
                vol_path = line.strip().split()[-1].split('/@')[0]
                break

        if not vol_path:
            raise ValueError(f'Folder path not retrieved: {vol_path}')

        LOGGER.info(f'Folder Path: {vol_path}')
        return vol_path

    @keyword('NAS: Utils: Get ZFS dir object id')
    def get_zfs_dir_object_id(self, pool_id, data_id):
        '''
        Fetching ZFS pool corresponding directory object id for error injection
        - This function is only for HERO NAS
        '''
        LOGGER.info(f'|___Fetching ZFS pool [{pool_id}] object id___|')
        cmd = (f"zdb -ddddd zpool{pool_id} {data_id} | grep -n dir_obj "
               "| grep -v init | awk '{print $4}'")
        dir_id = self.cli.run(cmd).strip()

        LOGGER.info(f'Object ID: [{dir_id}]\n')
        return dir_id

    @keyword('NAS: Utils: Create ZFS datapath')
    def create_zfs_datapath(self, pool_id, path_name, sync=None):
        '''
        Lib to create ZFS data path

        Arguments:
        | pool_id: Pool id where datapath to be created
        | path_name: Dataset path name to be created in pool
        | sync: sync write data with datapath  eg<sync=always>
        '''
        LOGGER.info('|___Create ZFS data path___|')

        data_path = f'zpool{pool_id}/{path_name}'
        cmd = f'zfs create {data_path}'
        if sync:
            cmd = f'zfs create -o sync={sync} {data_path}'
        self.cli.run(cmd)

        LOGGER.info(f'ZFS datapath {data_path} created\n')
        return data_path

    @keyword('NAS: Utils: Create ZFS snapshot')
    def create_zfs_snapshot(self, data_path, snap_name):
        '''
        Lib to create ZFS snapshot

        Arguments:
        | data_path: Dataset path for pool
        | snap_name: snapshot name
        '''
        LOGGER.info('|___Create ZFS snapshot___|')

        snap_path = f'{data_path}@{snap_name}'
        cmd = f'zfs snapshot {snap_path}'
        self.cli.run(cmd)

        LOGGER.info('ZFS snapshot created\n')
        return snap_path

    @keyword('NAS: Utils: Clone ZFS snapshot')
    def clone_zfs_snapshot(self, snap_path, pool_id, clone_name):
        '''
        Lib to clone the ZFS snapshot

        Arguments:
        | snap_path: Path where ZFS snapshot captured
        | pool_id: Storage pool ID
        | clone_name: Name of the clone path
        '''
        LOGGER.info('|___Clone ZFS snapshot___|')

        clone_path = f'zpool{pool_id}/{clone_name}'
        cmd = f'zfs clone {snap_path} {clone_path}'
        self.cli.run(cmd)

        LOGGER.info('Cloned ZFS snapshot\n')
        return clone_path

    @keyword('NAS: Utils: Promote ZFS snapshot')
    def promote_zfs_snapshot(self, clone_path):
        '''
        Lib to promote ZFS snapshot captured

        Arguments:
        | clone_path: ZFS snapshot clone path
        '''
        LOGGER.info('|___Promote ZFS snapshot___|')

        cmd = f'zfs promote {clone_path}'
        self.cli.run(cmd)

        LOGGER.info('ZFS snapshot promote is successful\n')
        return True

    @keyword('NAS: Utils: Search ZFS dataset id')
    def search_dataset_id(self, pool_id, search_str):
        '''
        Lib to search dataset id based on the occurance

        Arguments:
        | pool_id: Pool ID of NAS
        | search_str: String for which dataset id to be fetched
        '''
        LOGGER.info(f'|___Search {search_str} dataset ID___|')

        # Get dataset paths
        data_paths = self.get_zfs_pool_dataset_path(pool_id).split()
        search_result = [index for index, path in enumerate(data_paths)
                         if search_str in path and
                         'RecentlySnapshot' not in path]

        if not search_result:
            raise ValueError(f'{search_str} not found in:\n{data_paths}\n')
        if len(search_result) != 1:
            raise ValueError(f'Multiple {search_str} found in {data_paths}\n')

        # Get Dataset id
        dataset_ids = self.get_zfs_pool_dataset_id(pool_id).split()
        result_id = dataset_ids[int(search_result[0])]

        LOGGER.info(f'{search_str} dataset id: {result_id}\n')
        return result_id

    @keyword('NAS: Utils: Export ZFS pool')
    def export_zfs_pool(self, pool_id):
        '''
        Lib to export zfs pool (similar to reboot the NAS)
        '''
        LOGGER.info('|___Export ZFS Pool___|')

        cmd = f'zpool export zpool{pool_id}'
        self.cli.run(cmd)
        zpool_name = f'zpool{pool_id}'
        self.client.utils.run_keyword_expect_error(
            self.check_zpool_status, zpool_name=zpool_name, check_key='pool',
            expected_value=zpool_name)

        LOGGER.info('Export ZFS pool is successful\n')
        return True

    @keyword('NAS: Utils: Import ZFS pool')
    def import_zfs_pool(self, pool_id, replay_check=False,
                        enable_options=True):
        '''
        Lib to import zfs pool (Bringing NAS up after export)

        Arguments
        | pool_id:          Pool ID of the NAS storage
        | replay_check:     Boolean (True|False)
        |                   By default replay_check will be False (disabled),
        |                   To enable replay_check set replay_check to True
        | enable_options:   Boolean (True|False)
        |                   By default enable_options will be set True to
        |                   include options along with zpool import command.
        |                   Set enable_options as False to disable using
        |                   options along with zpool import command.
        '''
        LOGGER.info('|___Import ZFS Pool___|')

        cmd = f'zpool import zpool{pool_id} -f -N'

        if replay_check is True:
            cmd = f'zpool import -z zpool{pool_id} -f -N'

        if not enable_options:
            cmd = f'zpool import zpool{pool_id}'
        self.cli.run(cmd)
        # Check pool in ready state (online)
        self.client.utils.check_expected_pool(pool_id, expected_status='Ready')

        LOGGER.info('Import ZFS pool is successful\n')
        return True

    @keyword('NAS: Utils: Set ZFS zibcrypt debug flag')
    def set_zibcrypt_debug_flag(self, enable=False):
        """
        Enable/Disable zibcrypt debug flag
        - /sys/module/zfs/parameters/_vfs_zfs_zibcrypt_dbglevel
        """
        LOGGER.info('|__Set Zibcrypt Debug Flag__|')
        opt = 3 if enable is True else 0
        cmd = (f'echo {opt} > '
               '/sys/module/zfs/parameters/_vfs_zfs_zibcrypt_dbglevel')
        LOGGER.info(f'CMD [{cmd}]')
        self.cli.run(cmd)

        LOGGER.info(f'Zibcrypt debug flag set\n')
        return True

    @keyword('NAS: Utils: Set ZFS zilreplay disable flag')
    def set_zil_replay_disable_flag(self, enable=False):
        """
        Enable/Disable zil_replay_disable_flag

        Arguments
        | enable:   To enable zil replay disable flag set enable as True
        |           Set enable as False to disable zil replay disable flag
        """
        LOGGER.info('|___Set Zilreplay Disable Flag___|')
        opt = 0 if enable is True else 1
        cmd = (f'echo {opt} > '
               '/sys/module/zfs/parameters/_vfs_zfs_zil_replay_disable')
        LOGGER.info(f'CMD [{cmd}]')
        self.cli.run(cmd)

        LOGGER.info(f'Zibcrypt debug flag set\n')
        return True

    @keyword('NAS: Utils: Get ZFS name')
    def get_zfs_name(self, sharedfolder):
        '''
        Lib to get ZFS name from ZFS mount path

        Arguments:
        | sharedfolder: ZFS shared folder created in storage pool
        '''
        LOGGER.info(f'|___Get ZFS Name for {sharedfolder}___|')

        zfs_mount = self.get_folder_path(sharedfolder)
        zfs_vol = zfs_mount.split(f'/{sharedfolder}')[0]
        zfs_name = ''
        zfs_data = self.cli.run('zfs list').strip().splitlines()
        for line in zfs_data:
            if zfs_vol in line:
                zfs_name = line.split()[0]
                break

        if not zfs_name:
            raise ValueError(f'ZFS name not retrieved: {zfs_name}')

        LOGGER.info(f'ZFS name: {zfs_name}\n')
        return zfs_name

    @keyword('NAS: Utils: Clear ZFS handlers')
    def clear_zfs_handlers(self):
        '''
        Lib to clear ZFS handlers
        '''
        LOGGER.info('|___Clear ZFS handlers___|')

        cmd = 'zinject -c all'
        self.cli.run(cmd)

        LOGGER.info('Cleared ZFS handlers\n')
        return True

    @keyword('NAS: Utils: Execute ZFS fileclone')
    def execute_zfs_fileclone(self, src_file, dst_file, arg1, arg2, arg3):
        '''
        Lib to execute fileclone command

        Arguments:
        | src_file: Source file created at shared folder
        | dst_file: destination file created at shared folder
        | arg1: First argument to be passed to fileclone command
        | arg2: Second argument to be passed to fileclone command
        | arg3: Third argument to be passed to fileclone command
        '''
        LOGGER.info('|___Execute Fileclone Command___|')

        cmd = f'zfileclone {src_file} {dst_file} {arg1} {arg2} {arg3}'
        self.cli.run(cmd)

        LOGGER.info('Fileclone command executed\n')

    @keyword('NAS: Utils: Get ZFS metaspace percent')
    def get_zfs_metaspace_percent(self):
        '''
        Lib to get the ZFS metaspace percent value
        '''
        LOGGER.info('|___Get ZFS Metaspace Percent___|')

        cmd = 'cat /sys/module/zfs/parameters/' \
              '_vfs_zfs_deadlist_can_use_metaspace_percent'
        value = self.cli.run(cmd)

        LOGGER.info(f'ZFS metaspace percent value: {value}\n')
        return value

    @keyword('NAS: Utils: Get snapshot path')
    def get_snapshot_path(self, data_paths, snap_name):
        '''
        Lib to find the location of snap occurance in dataset path

        Arguments:
        | data_paths: ZFS pool dataset paths
        | snap_name: Name of snapshot
        '''
        LOGGER.info(f'|___Fetch snapshot path___|')

        snap_path = None
        for path in data_paths.split():
            if snap_name in path:
                snap_path = path
                break

        if snap_path is None:
            raise ValueError(f'{snap_name} not found in:\n{data_paths}\n')

        LOGGER.info(f'Snapshot path: {snap_path}\n')
        return snap_path

    @keyword('NAS: Utils: Destroy ZFS snapshot')
    def destroy_zfs_snapshot(self, snap_path):
        '''
        Lib to destroy ZFS snapshot

        Arguments:
        | snap_path: ZFS snapshot path
        '''
        LOGGER.info('|___Destroy ZFS snapshot___|')

        cmd = f'zfs destroy {snap_path}'
        self.cli.run(cmd)

        LOGGER.info('ZFS destroy snapshot is successful\n')
        return True

    @keyword('NAS: Utils: Hold ZFS snapshot')
    def hold_zfs_snapshot(self, snap_path):
        '''
        Lib to hold ZFS snapshot

        Arguments:
        | snap_path: ZFS snapshot path
        '''
        LOGGER.info('|___Hold ZFS snapshot___|')

        cmd = f'zfs hold keep {snap_path}'
        self.cli.run(cmd)

        LOGGER.info('ZFS hold snapshot is successful\n')
        return True

    @keyword('NAS: Utils: Freeze ZFS pool')
    def freeze_zfs_pool(self, pool_id):
        '''
        Lib to freeze zfs pool
        '''
        LOGGER.info('|___Freeze ZFS Pool___|')

        cmd = f'zpool freeze zpool{pool_id}'
        self.cli.run(cmd)

        LOGGER.info('Freeze ZFS pool is successful\n')
        return True

    @keyword('NAS: Utils: Get zpool vdev disks')
    def get_zpool_vdev_disks(self, zpool):
        '''
        Lib to get zpool vdev disks names

        Arguments:
        | zpool: zpool name   eg: <zpool2>
        '''
        LOGGER.info('|___Get zpool vdev disks___|')

        ret = self.cli.run(f'zpool status {zpool}')
        disks = [line.split()[0] for line in ret.splitlines() if
                 'disk_0x' in line and len(line) > 0]

        LOGGER.info(f'Retrieved vdev disks: {disks}\n')
        return disks

    @keyword('NAS: Utils: Create zpool')
    def create_zpool(self, zpool_name, disk_type='hdd', raid_level='0',
                     raid_disks=None, raid_disk_num=None):
        '''
        Lib to create zpool

        Arguments
        | zpool_name: Name of the zpool
        | disk_type: hdd / ssd
        | raid_level: 0 / 1 / 5 / 6 ...
        | raid_disks: diskID (if not provide, auto select disks)
        | raid_disk_num:  how many disks to build that raid (if not provided,
        |                 select minimum raid disk requirement)
        '''
        LOGGER.info('|___Create zpool___|')

        if not raid_disks:
            free_disks = self.client.qcli.get_disk(disk_type)
            raid_disks = self.client.qcli.pick_raid_disk(
                raid_level, free_disks, raid_disk_num)

        raid_disks = raid_disks.split(',')
        vdev_list = self.client.utils.get_disk_sys_name(raid_disks)
        vdev_names = ' '.join([f'{vd}3' for vd in vdev_list])
        cmd = f'zpool create -f {zpool_name} {vdev_names}'
        self.cli.run(cmd)

        LOGGER.info(f'zpool {zpool_name} created successfully!\n')
        return True

    @keyword('NAS: Utils: Destroy zpool')
    def destroy_zpool(self, zpool_name):
        '''
        Lib to delete zpool
        '''
        LOGGER.info(f'|___Destroy zpool {zpool_name}___|')

        zpool_status = self.cli.run('zpool status')

        # Destroys zpool only if its info exists in zpool status
        if zpool_name in zpool_status:
            cmd = f'zpool destroy {zpool_name}'
            self.cli.run(cmd)

        LOGGER.info(f'zpool {zpool_name} is deleted successfully!\n')
        return True

    @keyword('NAS: Utils: Get dataset property value')
    def get_dataset_property_value(self, datapath, check_property='type'):
        '''
        Lib to get dataset property value

        Arguments
        | datapath: zfs dataset path
        | check_property: zfs dataset property value to be fetched (e.g: utf-8,
        |           case-sensitivity, normalization.)
        '''
        LOGGER.info(f'|___Fetch dataset property {check_property} value___|')

        cmd = f'zfs get {check_property} {datapath}'
        out = self.cli.run(cmd)
        # Example output
        # NAME             PROPERTY         VALUE        SOURCE
        # zpool2/dataset1  casesensitivity  insensitive  -

        # Get VALUE from the output
        lines = out.strip().split('\n')
        keys = lines[0].split()
        values = lines[1].split()
        index = keys.index('VALUE')
        value = values[index]

        LOGGER.info(f'Dataset property {check_property}: {value}\n')
        return value

    @keyword('NAS: Utils: Create dataset on zpool')
    def create_dataset_on_zpool(self, zpool_name, dataset, options=''):
        '''
        Lib to create dataset on zpool

        Arguments
        | zpool_name:   zpool name
        | dataset:      Name of the dataset to be created in zpool
        '''
        LOGGER.info('|___Create dataset on zpool___|')

        data_path = f'{zpool_name}/{dataset}'
        cmd = f'zfs create {options} {data_path}'
        self.cli.run(cmd)

        LOGGER.info(f'Dataset created on {data_path}\n')
        return data_path

    @keyword('NAS: Utils: Mount ZFS datapath')
    def mount_zfs_datapath(self, datapath):
        '''
        Lib to mount ZFS datapath

        Arguments
        | datapath: ZFS datapath to be mounted eg. <zpool2/fs>
        '''
        LOGGER.info('|___Mount ZFS Datapath___|')

        cmd = f'zfs mount {datapath}'
        self.cli.run(cmd)

        LOGGER.info('Mounted ZFS datapath successfully\n')
        return True

    @keyword('NAS: Utils: Rollback ZFS snapshot')
    def rollback_zfs_snapshot(self, snap_path):
        '''
        Lib to rollback ZFS snapshot

        Arguments:
        | snap_path: ZFS snapshot path
        '''
        LOGGER.info('|___Rollback ZFS snapshot___|')

        cmd = f'zfs rollback {snap_path}'
        self.cli.run(cmd)

        LOGGER.info('ZFS rollback snapshot is successful\n')
        return True

    @keyword('NAS: Utils: Get ZFS snap send and recieve status')
    def get_zfs_snap_send_recv_status(self, snap_file, to_path):
        '''
        Lib to get zfs snap sent and recieve status

        Arguments:
        | snap_file:    Source file of the snapshot
        | to_path:      Destination path of the snapshot
        '''
        LOGGER.info('|___Fetch ZFS snapshot send and recieve status___|')

        cmd = f'zfs send {snap_file} | zfs recv {to_path}'
        out = self.cli.run(cmd)

        LOGGER.info(f'ZFS send and recv status: {out}\n')
        return True

    @keyword('NAS: Utils: Get richacl of file')
    def get_richacl_of_file(self, filename):
        '''
        Lib to get the Rich access control lists of a file

        Arguments:
        | filename: Name of the file
        '''
        LOGGER.info('|___Get ZFS richacl of a file___|')

        cmd = f'richacl -g {filename}'
        out = self.cli.run(cmd)

        LOGGER.info(f'ACL of the file {filename}: {out}\n')
        return out

    @keyword('NAS: Utils: Umount ZFS datapath')
    def umount_zfs_dataset(self, datapath):
        '''
        Lib to unmount zfs datapath

        Arguments
        | datapath: ZFS datapath to be unmounted eg. <zpool2/fs>
        '''
        LOGGER.info('|___Unmount ZFS datapath___|')

        cmd = f'zfs umount {datapath}'
        self.cli.run(cmd)

        LOGGER.info('Unmounted ZFS datapath successfully!\n')
        return True

    @keyword('NAS: Utils: Check utf8only property')
    def check_utf8only_property(self, datapath, expected_value='off'):
        '''
        Lib to check utf-8 case property

        Arguments
        | datapath:         Path of the dataset (eg zpool_name/dataset)
        | expected_value:   on | off (default=off)
        '''
        LOGGER.info('|___Check utf8only property___|')

        prop_value = self.get_dataset_property_value(
            datapath, check_property='utf8only')

        if expected_value.lower() != prop_value.lower():
            raise ValueError(f'Not found utf8only property as {expected_value}'
                             f' but got {prop_value}!')

        self.cli.run(f'cd {datapath} && rm -rf folder')
        self.cli.run(f'cd {datapath} && mkdir folder')

        if expected_value == 'on':
            self.client.utils.run_keyword_expect_error(
                self.cli.run, f"cd {datapath}/folder && touch $'\\377'")
        else:
            self.cli.run(f"cd {datapath}/folder && touch $'\\377'")

        LOGGER.info(f'Expected utf8only property occurs!\n')
        return True

    @keyword('NAS: Utils: Check casesensititvity property')
    def check_casesensititvity_property(self, datapath,
                                        expected_value='sensitive'):
        '''
        Check case sensitivity property

        Arguments
        | datapath:         Path of the dataset (eg zpool_name/dataset)
        | expected_value:   sensitive | insensitive (default=sensitive)
        '''
        LOGGER.info('|___Check casesensitivity property___|')

        prop_value = self.get_dataset_property_value(
            datapath, check_property='casesensitivity')

        if expected_value.lower() != prop_value.lower():
            raise ValueError(f'Not found casesensitivity as {expected_value} '
                             f'but got {prop_value}!')

        self.cli.run(f'cd {datapath} && rm -rf folder && rm -rf FOLDER')
        self.cli.run(f'cd {datapath} && mkdir folder')

        if expected_value == 'insensitive':
            self.client.utils.run_keyword_expect_error(
                self.cli.run, f'cd {datapath} && mkdir FOLDER')
        else:
            self.cli.run(f'cd {datapath} && mkdir FOLDER')

        cmd = f'cd {datapath} && ls -li'
        out = self.cli.run(cmd)
        LOGGER.info(f'Output of {cmd}: {out}')

        LOGGER.info(f'Expected casesensitivity property occurs!\n')
        return True

    @keyword('NAS: Utils: Check normalization property')
    def check_normalization_property(self, datapath, expected_value='none'):
        '''
        Check normalization property

        Arguments
        | datapath:         Path of the dataset (eg zpool_name/dataset)
        | expected_value:   none | formC | formD  (default=none)
        '''
        LOGGER.info('|___Check normalization property___|')

        prop_value = self.get_dataset_property_value(
            datapath, check_property='normalization')

        if expected_value.lower() != prop_value.lower():
            raise ValueError(f'Not found normalization as {expected_value} '
                             f'but got {prop_value}!')

        LOGGER.info(f'Expected normalization property occurs!\n')
        return True

    @keyword('NAS: Utils: Get ZFS dataset blocksize')
    def get_zfs_dataset_blocksize(self, dataset):
        '''
        Lib to get ZFS dataset blocksize

        Arguments
        | dataset: Dataset path of zpool    eg: <zpool2/zfs274>
        '''
        LOGGER.info('|___Get ZFS dataset blocksize___|')

        size = self.cli.run(f'zfs get all {dataset} '
                            f'| grep volblocksize').split()[-2]
        block_size = tool.tool.conv_to_basesize(size)

        LOGGER.info(f'Blocksize of dataset: {block_size}\n')
        return block_size

    @keyword('NAS: Utils: Get ZFS dataset path with ignore string')
    def get_path_with_ignore_string(self, pool_id, ignore_str):
        '''
        Lib to get dataset path while ignoring few paths based on string
        eg: Complete dataset paths:
        zpool2/zfs274@snapshot1
        zpool2/zfs274@snapshot2
        zpool2/zfs274
        zpool2/zfs275

        ignore_str = snapshot

        Output after ignore_str:
        zpool2/zfs274
        zpool2/zfs275

        Arguments
        | pool_id: Pool ID of the NAS
        | ignore_str: str to be used to ignore the data paths
        '''
        LOGGER.info('|___Get Dataset Paths with ignore string___|')

        cmd = (f"zdb -d zpool{pool_id} | grep -v {ignore_str} "
               "| grep -v init | grep -n ZVOL | awk '{print $2}'")
        path = self.cli.run(cmd).strip()
        if not path:
            cmd = (f"zdb -d zpool{pool_id} | grep -v {ignore_str} "
                   "| grep -v init | grep -n ZPL | awk '{print $2}'")
            path = self.cli.run(cmd).strip()

        LOGGER.info(f'Dataset path [{path}]\n')
        return path

    @keyword('NAS: Utils: Copydiff ZFS snapshots')
    def copydiff_zfs_snapshots(self, snap1, snap2, data_path):
        '''
        Lib to copy diffs for ZFS snapshots

        Arguments
        | snap1: complete path of snapshot 1     eg:<zpool2/zfs274@snapshot1>
        | snap2: complete path of snapshot 2     eg:<zpool2/zfs274@snapshot2>
        | data_path: Path where diff to be copied   eg: <zpool2/zfs275>
        '''
        LOGGER.info('|___Copydiff ZFS snapshots___|')

        self.cli.run(f'zfs copydiff {snap2} {snap1} {data_path}')

        LOGGER.info('ZFS copydiff snapshot executed successfully..\n')
        return True

    @keyword('NAS: Utils: Search ZFS dataset path')
    def search_dataset_path(self, pool_id, search_str):
        '''
        Lib to search dataset path based on search string

        Arguments:
        | pool_id: Pool ID of NAS
        | search_str: String for which dataset path to be fetched
        '''
        LOGGER.info(f'|___Search {search_str} dataset path___|')

        # Get dataset paths
        data_paths = self.get_zfs_pool_dataset_path(pool_id).split()
        search_result = [path for path in data_paths
                         if search_str in path and
                         'RecentlySnapshot' not in path]

        if not search_result:
            raise ValueError(f'{search_str} not found in:\n{data_paths}\n')
        if len(search_result) != 1:
            raise ValueError(f'Multiple {search_str} found in {data_paths}')

        LOGGER.info(f'{search_str} dataset path: {search_result[0]}\n')
        return search_result[0]

    @keyword('NAS: Utils: Set dataset property value')
    def set_dataset_property_value(self, datapath, dataset_prop, value):
        '''
        Lib to set dataset property value

        Arguments
        | dataset_name: Name of the dataset whose property has to be set
        | dataset_prop: Property of the dataset
        | value: Value of the property to be set.
        '''
        LOGGER.info(f'|___Set dataset property {dataset_prop} to {value}___|')

        cmd = f'zfs set {dataset_prop}={value} {datapath}'
        self.cli.run(cmd)

        LOGGER.info(f'Property {dataset_prop} set to {value} successfully\n')
        return True

    @keyword('NAS: Utils: Set zpool vdev offline')
    def set_zpool_vdev_offline(self, zpool, disks):
        '''
        Remove a disk from the zpool
        Arguments
        | pool: pool id eg:<2>
        | disks: zpool vdev disks
        '''
        LOGGER.info(f'|___Set {zpool} vdev offline___|')

        cmd = f'zpool offline -t zpool{zpool} {disks}'
        self.cli.run(cmd)

        LOGGER.info(f'{disks} removed succesfully\n')
        return True

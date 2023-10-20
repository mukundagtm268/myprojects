#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=redefined-builtin, unused-argument, invalid-name
from typing import TYPE_CHECKING
import tool.tool as tool
from baselib.robotlogger import RobotLogger
from baselib.robotkeyword import keyword
LOGGER = RobotLogger(__name__)

if TYPE_CHECKING:
    from .main import NAS


class Setup(object):

    def __init__(self, client: "NAS"):
        self.client = client

    @property
    def product(self):
        return self.client.product

    @property
    def qcli(self):
        return self.client.qcli

    @property
    def qpkg(self):
        return self.client.qpkg

    @keyword('NAS: Setup: Clean environment')
    def clean_env(self):
        '''
        Clean up NAS environment but keep major pool / volume, including
        - Restore all unplugged drives
        - Recover possible disk error after error injection
        - Delete all iscsi backup/restore jobs
        - Delete all snapsync jobs
        - Delete all virtual disks
        - Delete cache pool
        - Delete all users from NAS except admin
        - Delete all iscsi targets
        - Delete all LUNs
        - Delete all volume and pool
        - Disable all global spare disks
        '''
        self.client.utils.plug_in_disk()
        self.client.utils.recover_raid_disks_error(timeout=240)
        self.qcli.hdd.disable_all_enclosure_spare()
        self.qcli.iscsibackup.delete_all_jobs()
        self.client.utils.check_jobs_expected_state('updated', timeout=500)
        self.qcli.snapsync.delete_all_job()
        self.qcli.virtualdisk.delete_all()
        self.qcli.cache.remove()
        self.qcli.users.delete_all()
        self.qcli.iscsi.remove_all_targets()
        self.qcli.iscsi.remove_all_luns()
        if self.product == 'HERO':
            sys_storage = self.qcli.pool.get_system_pool()
            self.qcli.pool.remove_all(ignore_pool=sys_storage)
        elif self.product == 'TS':
            self.qcli.pool.remove_all_but_keep_major_pool(force=True)
            self.qcli.volume.remove_all_but_keep_major_vol()

    @keyword('NAS: Setup: Clean iSCSI objects')
    def clean_iscsi(self):
        '''
        Clean up NAS iSCSI targets and lun
        '''
        self.qcli.iscsi.remove_all_targets()
        self.qcli.iscsi.remove_all_luns()

    def _convert_raidlevel(self, raid_level):
        if raid_level is None:
            raid_level = 'Single'
        raid_level = str(raid_level)
        if self.product == 'HERO':
            # HERO not support raid Single, convert to 0
            raid_level = '0' if raid_level == 'Single' else raid_level
        return raid_level

    @keyword('NAS: Setup: Create system storage')
    def create_system_storage(self, disktype='hdd', raid_level=None,
                              raid_disks=None, raid_disk_num=None):
        '''
        Create system storage for NAS
        - NAS == HERO, create system pool
        - NAS == TS, create static volume

        If system storage exists, will skip creation and \
return the pool / volume ID directly
        '''
        raid_level = self._convert_raidlevel(raid_level)
        if self.product == 'HERO':
            sys_storage = self.qcli.pool.get_system_pool()
            if sys_storage is None:
                sys_storage = self.qcli.pool.create(
                    disktype=disktype, raid_level=raid_level,
                    raid_disks=raid_disks, raid_disk_num=raid_disk_num)
        elif self.product == 'TS':
            sys_storage = self.qcli.volume.get_major_volume()
            if sys_storage is None:
                sys_storage = self.qcli.volume.create_static(
                    disktype=disktype, raid_level=raid_level,
                    raid_disks=raid_disks, raid_disk_num=raid_disk_num)
        return sys_storage

    @keyword('NAS: Setup: Enable iSCSI service')
    def enable_iscsi_service(self):
        '''
        Enable iSCSI service on NAS
        '''
        self.qcli.iscsi.enable_setting()
        return True

    @keyword('NAS: Setup: Install QsyncServer QPKG')
    def install_qsync_qpkg(self):
        '''
        Install QsyncServer QPKG on NAS
        '''
        qpkgs = self.qpkg.list(show=False)
        exist = True if 'QsyncServer' in qpkgs else False
        if not exist:
            self.qpkg.add('QsyncServer')
        return True

    @keyword('NAS: Setup: Install SystemTap QPKG')
    def install_stap_qpkg(
         self, qpkg_name, server_ip, server_path,
         local_path=None, username=None, password=None, version='1.0'):
        '''
        Install SystemTap QPKG from remote server onto NAS
        - If username and password provided, mount with CIFS
        - Else mount with NFS
        '''
        qpkgs = self.qpkg.list(show=False)
        exist = True if 'SystemTap' in qpkgs else False
        if not exist:
            path = self.client.mount(
                server_ip=server_ip, server_path=server_path,
                local_path=local_path, username=username,
                password=password, version=version)
            self.qpkg.install(f'{path}/{qpkg_name}')
            self.client.umount(path)
        return True

    @keyword('NAS: Setup: Create pool')
    def create_pool(self, disktype='hdd', raid_level='1',
                    raid_disks=None, raid_disk_num=None):
        '''
        Create pool on NAS
        Arguments
        | disktype = hdd / ssd / SATA / NL-SAS
        | (if not provide, auto select disks)
        | raid_level = Single (TS-only) / 0 / 1 / 5 / 6 / 50 / 60 ..
        | raid_disk = diskID (if not provide, auto select disks)
        | raid_disk_num = how many disks to build tha raid (if not provide,
        | select minimum raid disk requirement)
        '''
        raid_level = self._convert_raidlevel(raid_level)
        kwargs = tool.passing_func_args(locals())
        pool_id = self.qcli.pool.create(**kwargs)
        return pool_id

    @keyword('NAS: Setup: Set Rebuild Priority')
    def set_rebuild_priority(self, pool_id, speed='high'):
        '''
        Sets rebuild priority

        Arguments
        | pool_id: pool ID for which rebuild priority has to be set
        | speed:   low, medium or high
        |          shall set specified rebuild priority
        '''
        LOGGER.info(f'|___Set Rebuild Priority to {speed}___|')

        # Sets value for service first rebuild priority
        if speed == 'low':
            resilver_ratio = 10
            scrub_ratio = 10

        # Sets value for default rebuild priority
        elif speed == 'medium':
            resilver_ratio = 50
            scrub_ratio = 50

        # Sets value for Resync first rebuild priority
        else:
            resilver_ratio = 90
            scrub_ratio = 90

        # Run the command to set rebuild priority
        self.client.cli.run(f"/sbin/zpool set 'resilver_ratio="
                            f"{resilver_ratio}' zpool{pool_id}")
        self.client.cli.run(f"/sbin/zpool set 'scrub_ratio={scrub_ratio}'"
                            f" zpool{pool_id}")

        LOGGER.info('SUCCESS: Rebuild priority is set\n')
        return True

    @keyword('NAS: Setup: Create target')
    def create_target(self, name=None, alias=None, interface=None,
                      target_header_digest='no', target_data_digest='no'):
        '''
        Create target on NAS
        - interface option only for TS client
        '''
        if self.product == 'HERO':
            target_id = self.qcli.iscsi.create_target(
                name=name, alias=alias,
                target_header_digest=target_header_digest,
                target_data_digest=target_data_digest)
        elif self.product == 'TS':
            target_id = self.qcli.iscsi.create_target(
                name=name, alias=alias, interface=interface,
                target_header_digest=target_header_digest,
                target_data_digest=target_data_digest)
        return target_id

    @keyword('NAS: Setup: Create block-based LUN')
    def create_block_lun(
         self, pool_id, capacity='5GB', allocation='Thin', name=None):
        '''
        Create block LUN on NAS
        - allocation = Thin / Thick
        '''
        if self.product == 'HERO':
            lun_id = self.qcli.iscsi.create_lun(
                pool_id=pool_id, capacity=capacity,
                allocation=allocation, name=name)
        elif self.product == 'TS':
            lun_id = self.qcli.iscsi.create_block_lun(
                pool_id=pool_id, capacity=capacity,
                allocation=allocation, name=name)
        return lun_id

    @keyword('NAS: Setup: Enable LUN')
    def enable_lun(self, lun_id):
        '''
        Enable LUN on NAS
        '''
        self.qcli.iscsi.enable_lun(lun_id)
        return True

    @keyword('NAS: Setup: Disable LUN')
    def disable_lun(self, lun_id):
        '''
        Disable LUN on NAS
        '''
        self.qcli.iscsi.disable_lun(lun_id)
        return True

    @keyword('NAS: Setup: Map LUN to target')
    def map_lun(self, lun_id, target_id):
        '''
        Map LUN to target on NAS
        '''
        self.qcli.iscsi.map(lun_id, target_id)
        return True

    @keyword('NAS: Setup: Unmap LUN from target')
    def unmap_lun(self, lun_id, target_id):
        '''
        Unmap LUN from target on NAS
        '''
        self.qcli.iscsi.unmap(lun_id, target_id)
        return True

    @keyword('NAS: Setup: Get targetIQN by targetID')
    def get_target_iqn_by_id(self, target_id):
        '''
        Get target IQN by target ID on NAS
        '''
        if self.product == 'HERO':
            iqn = self.qcli.iscsi.get_target_iqn(target_id)
        elif self.product == 'TS':
            iqn = self.qcli.iscsi.get_target_iqn_by_id(target_id)
        return iqn

    @keyword('NAS: Setup: Check target connected')
    def check_target_connected(self, target_id):
        '''
        Check if target status == connected
        - Normally use after another client connect to the NAS target
        '''
        LOGGER.info('|___Check Target Connected___|')
        LOGGER.info(f'Target [{target_id}]')
        check_status = self.qcli.check_status(
            expected_value='Connected',
            func=self.qcli.iscsi.target_info,
            target_id=target_id,
            action='get',
            section='overview',
            column='Status',
            sleeptime=2,
            timeout=30)

        if not check_status:
            raise ValueError('Target not connected!')

        LOGGER.info('Target connected!\n')
        return True

    @keyword('NAS: Setup: Create ZFS shared folder')
    def create_sharedfolder(self, pool_id, sharename=None, type='thin',
                            size='5GB', compression='yes', deduplication='no',
                            encrypt='no', encrypt_key='', encrypt_savekey='no',
                            qsync=None, worm='no', worm_retention=1,
                            worm_format='day', worm_lock_hour=0,
                            worm_lock_minute=1, syncronize='Auto'):
        '''
        Create sharedfolder (volume) on HERO NAS
        - This method is only for HERO
        '''
        kwargs = tool.passing_func_args(locals())
        return self.qcli.sharedfolder.create(**kwargs)

    @keyword('NAS: Setup: Set global spare disk')
    def set_global_spare(self, enslosure_id=None, disktype='hdd'):
        '''
        Set global spare disk on NAS
        '''
        disk_id = self.qcli.hdd.pick_spare_disk(enslosure_id, disktype)
        # check and update disk volume config
        self.client.utils.check_update_disk_volume_conf(disk_id)
        return self.qcli.hdd.set_enclosure_spare(disk_id, enable='Enabled')

    @keyword('NAS: Setup: Set pool hot spare disk')
    def set_hot_spare(self, pool_id, disktype='hdd'):
        '''
        Set hot spare disk for pool on NAS
        - This method is only for HERO
        '''
        kwargs = tool.passing_func_args(locals())
        return self.qcli.pool.enable_hot_spare(**kwargs)

    @keyword('NAS: Setup: Add iscsi backup job')
    def add_iscsi_backup_job(self, lun_id, job_name=None, image_name=None,
                             compression='no', protocol=2, server=None,
                             path=None, username=None, password=None,
                             schedule=1, minute=None,
                             hour=None, week_day=None, month_day=None,
                             wait=False):
        '''
        Library to create iscsi backup job
        '''
        kwargs = tool.passing_func_args(locals())
        job_id = self.qcli.iscsibackup.add_backup_job(**kwargs)
        return job_id

    @keyword('NAS: Setup: Add iscsi restore job')
    def add_iscsi_restore_job(self, path=None, image_name=None, job_name=None,
                              dedup=None, dest_lun_type='new',
                              new_lun_name=None, pool_id=None, lun_id=None,
                              protocol=2, server=None, username=None,
                              password=None, wait=False):
        '''
        Library to add iscsi restore job
        '''
        kwargs = tool.passing_func_args(locals())
        job_id = self.qcli.iscsibackup.add_restore_job(**kwargs)
        return job_id

    @keyword('NAS: Setup: Get iscsi job name')
    def get_iscsi_job_image(self, job_id):
        '''
        Library to ge the ISCSI Job image name
        '''
        image = self.qcli.iscsibackup.job_image(job_id=job_id)
        return image

    @keyword('NAS: Setup: Edit NFS service')
    def edit_nfs_service(self, enable=None, enable_v4=None):
        '''
        Library to edit NFS server options
        '''
        kwargs = tool.passing_func_args(locals())
        self.qcli.networkservice.edit_nfs_service(**kwargs)
        return True

    @keyword('NAS: Setup: Set NFS')
    def set_nfs(self, sharename, access='Enabled'):
        '''
        Library to set the NFS permission for shared folder
        '''
        kwargs = tool.passing_func_args(locals())
        self.qcli.sharedfolder.set_nfs(**kwargs)
        return True

    @keyword('NAS: Setup: Add NFS')
    def add_nfs(self, sharename, hostip, permission=None, squash=None,
                anonymous_gid=None, anonymous_uid=None, sync=None, secure=None,
                wdelay=None):
        '''
        Lib to add NFS host access
        '''
        kwargs = tool.passing_func_args(locals())
        self.qcli.sharedfolder.add_nfs(**kwargs)
        return True

    @keyword('NAS: Setup: Add virtual disk')
    def add_virtual_disk(self, target_iqn=None, target_name=None, lun_id=None,
                         vddname=None, ip='127.0.0.1', port='3260',
                         authentication='no', auth_id=None,
                         auth_pwd=None, header_digest='no', data_digest='no',
                         doformat='yes', filesystem='EXT3'):
        '''
        Lib to add virtual disk to NAS
        '''
        kwargs = tool.passing_func_args(locals())
        vddname = self.qcli.virtualdisk.add(**kwargs)
        return vddname

    @keyword('NAS: Setup: Get virtual disk info')
    def get_vd_info(self, action='print', section='all', column=None,
                    diskname=None, targetip=None):
        '''
        Lib to get the Virtual Disk LUN details
        '''
        kwargs = tool.passing_func_args(locals())
        lun = self.qcli.virtualdisk.disk_list(**kwargs)
        return lun

    @keyword('NAS: Setup: Take ISCSI snapshot')
    def take_iscsi_snapshot(self, lun_id, snapshot_name=None, snapshot_type=0,
                            vital=None, description='test'):
        '''
        Lib to take ISCSI snapshot
        '''
        kwargs = tool.passing_func_args(locals())
        snap_id = self.qcli.iscsisnapshot.take(**kwargs)
        return snap_id

    @keyword('NAS: Setup: Delete all ISCSI snapshots')
    def delete_all_iscsi_snapshots(self, lun_id):
        '''
        Lib to delete all the ISCSI snapshots of the LUN
        '''
        self.qcli.iscsisnapshot.delete_all(lun_id)
        return True

    @keyword('NAS: Setup: Get LUN info')
    def get_lun_info(self, lun_id, action='print', section='all', column=None):
        '''
        Lib to get the lun info details
        '''
        info = self.qcli.iscsi.lun_info(lun_id, action, section, column)
        return info

    @keyword('NAS: Setup: Lock shared folder')
    def lock_sharedfolder(self, sharename):
        '''
        Lib to lock the encrypted shared folder
        '''
        self.qcli.encrypt.lock_sharefolder(sharename)
        return True

    @keyword('NAS: Setup: Unlock shared folder')
    def unlock_sharedfolder(self, sharename, keystr=None, keyfile=None):
        '''
        Lib to unlock the encrypted shared folder
        '''
        kwargs = tool.passing_func_args(locals())
        self.qcli.encrypt.unlock_sharefolder(**kwargs)
        return True

    @keyword('NAS: Setup: Create cache pool')
    def create_cache_pool(
            self, disk_id=None, raid_level='0', raid_disk_num=None,
            cache_type='0', volume_id=None, disk_type='ssd'):
        '''
        Lib to create cache pool
        '''
        kwargs = tool.passing_func_args(locals())
        cache_id = self.qcli.cache.create(**kwargs)
        return cache_id

    @keyword('NAS: Setup: Get Volume info')
    def get_volume_info(self, action='print', section='all', column=None,
                        sharename=None):
        '''
        Lib to get the volume info detials
        '''
        kwargs = tool.passing_func_args(locals())
        info = self.qcli.sharedfolder.volume_info(**kwargs)
        return info

    @keyword('NAS: Setup: Set cache')
    def set_cache(self, blv_id, enable='Enabled'):
        '''
        Lib to enable/disable cache for volumes/luns
        '''
        self.qcli.cache.set_cache_for(blv_id, enable)
        return True

    @keyword('NAS: Setup: Take volume snapshot')
    def take_volume_snapshot(self, sharename, snapshot_name=None, vital=None,
                             description='test'):
        '''
        Lib to take volume snapshot
        '''
        kwargs = tool.passing_func_args(locals())
        snap_id = self.qcli.sharedfoldersnapshot.take(**kwargs)
        return snap_id

    @keyword('NAS: Setup: Delete all volume snapshots')
    def delete_all_volume_snapshots(self, sharename):
        '''
        Lib to delete volume snapshot
        '''
        self.qcli.sharedfoldersnapshot.delete_all(sharename)
        return True

    @keyword('NAS: Setup: Get cache folder BLV ID')
    def get_folder_blv_id(self, sharename):
        '''
        Lib to get folder BLV ID to set for cache pool
        '''
        blv_id = self.qcli.cache.get_sharedfolder_blv_id(sharename)
        return blv_id

    @keyword('NAS: Setup: Edit NFS access')
    def edit_nfs_access(self, sharename, old_hostip, new_hostip=None,
                        permission=None, squash=None, anonymous_gid=None,
                        anonymous_uid=None, secure=None, sync=None,
                        wdelay=None, random_options=False):
        '''
        Lib to edit NFS access for shared folder
        '''
        kwargs = tool.passing_func_args(locals())
        self.qcli.sharedfolder.edit_nfs(**kwargs)
        return True

    @keyword('NAS: Setup: Edit advance MS network')
    def edit_advance_ms_network(
            self, enable_winserver=None, use_specific_winserver=None,
            winserver_ip=None, local_master_browser=None,
            allow_only_ntlmv2=None, name_resolve_priority=None,
            login_style=None, auto_register_dns=None, enable_trust_domain=None,
            enable_aio=None, smb_version=None, enable_smb2=None,
            enable_kernel_mode_smb=None):
        '''
        Lib to edit advanced Microsoft network options.
        '''
        kwargs = tool.passing_func_args(locals())
        self.qcli.networkservice.edit_advanced_ms_network(**kwargs)
        return True

    @keyword('NAS: Setup: Add users')
    def add_users(self, username=None, password='qnapqnap',
                  email='qnap@evt.com', sendmail='Disabled',
                  description='test', groupname=None, afp='Enabled',
                  ftp='Enabled', samba='Enabled', webdav='Enabled',
                  wfm='Enabled', readonly=None, readwrite=None,
                  denyaccess=None):
        '''
        Lib to add users in NAS
        '''
        kwargs = tool.passing_func_args(locals())
        username = self.qcli.users.add(**kwargs)
        return username

    @keyword('NAS: Setup: Delete users')
    def delete_users(self, username, delete_homefolder=True):
        '''
        Lib t delete users created in NAS for testing
        '''
        self.qcli.users.delete(username, delete_homefolder)
        return True

    @keyword('NAS: Setup: Add sharedfolder usergroup permission')
    def add_usergroup_permission(self, sharename, userrw=None, userrd=None,
                                 userno=None, grouprw=None, grouprd=None,
                                 groupno=None, domain_userrw=None,
                                 domain_userrd=None, domain_userno=None,
                                 domain_grouprw=None, domain_grouprd=None,
                                 domain_groupno=None, domain_computerrw=None,
                                 domain_computerrd=None,
                                 domain_computerno=None):
        '''
        Lib to add user group permissions for sharedfolder
        '''
        kwargs = tool.passing_func_args(locals())
        self.qcli.sharedfolder.add_usergroup(**kwargs)
        return True

    @keyword('NAS: Setup: Edit target')
    def edit_target(self, target_id, alias=None,
                    target_header_digest=None, target_data_digest=None):
        '''
        Lib to edit ISCSI target
        '''
        kwargs = tool.passing_func_args(locals())
        target_id = self.qcli.iscsi.edit_target(**kwargs)
        return target_id

    @keyword('NAS: Setup: Get cache info')
    def get_cache_info(
            self, action='print', section='all', column=None, pool_id=None):
        '''
        Lib to get cache info
        '''
        kwargs = tool.passing_func_args(locals())
        info = self.qcli.cache.info(**kwargs)
        return info

    @keyword('NAS: Setup: Recover raid group')
    def recover_raid_group(self, pool_id):
        '''
        Lib to recover raid group
        '''
        raid_id = self.qcli.raid.get_pool_raid_id(pool_id)
        self.qcli.raid.recover(raid_id)
        return True

    @keyword('NAS: Setup: Set snapsync service')
    def set_snapsync_service(
            self, enable='Enabled', port=None, bandwidth=None):
        '''
        Lib to enable/disable snapsync service
        '''
        self.qcli.snapsync.set_service(enable, port, bandwidth)
        return True

    @keyword('NAS: Setup: Create snapsync job')
    def create_snapsync_job(
            self, jobname=None, remote_site='127.0.0.1',
            secure_connection='no', username='admin', password='qnapqnap',
            port='8080', sharename=None, local_vol_id=None, local_lun_id=None,
            dst_pool=None, remote_drive=None, deduplication=None, snaptype=1,
            compression=None, real_time=0, encryption=None, execute_now=0,
            adapter_mode=1, src_ip=None, dst_ip=None, src_failover_ip=None,
            dst_failover_ip=None, key_str=None):
        '''
        Lib to create snapsync job
        '''
        kwargs = tool.passing_func_args(locals())
        job_id = self.qcli.snapsync.create_job(**kwargs)
        return job_id

    @keyword('NAS: Setup: Enable SMART migration')
    def enable_smart_migration(self):
        '''
        Lib to get smart migration enabled status and if not enabled enable it
        '''
        enable_status = self.qcli.hdd.smart_migration_info(
            action='get', section='overview', column='all')

        # Enable smart migration if the enable status is not enabled
        if enable_status['enable'] == 'no':
            self.qcli.hdd.set_smart_migration(enable='Enabled')

        LOGGER.info(f'Predictive SMART Migration is enabled!\n')
        return True

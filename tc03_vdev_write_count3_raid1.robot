*** Settings ***
Documentation  A RF test suite to run error injection tests
...            Created by Mukunda
Resource       ../../Keywords/Main.robot

Force Tags   vdev_write  vdev_write_err_inj_tc03
Suite Setup  Run Keywords
...          ErrInj: Load NAS Client  ${NAS_IP}  ${NAS_USER}  ${NAS_PWD}  AND
...          Threads: Clear Threads
Test Setup   Run Keywords
...          Skip If Previous Test Fail  AND
...          NAS: Utils: Clear Dmesg And Hide Output
Test Teardown  NAS: Utils: Save Debug Information

*** Variables ***
# NAS data
${NAS_IP}      ${None}
${NAS_USER}    admin
${NAS_PWD}     ${None}

# Stap data
${STAP_PATH}   zfs\\vdev
${STAP_FILE}   vdev_write_error_H5.0.1.stp

# Pool config
${DISK_TYPE}   hdd
${RAID_LEVEL}  1
${DISK_NUM}    2

# Shared folder config
${FOLDER_TYPE}  thin
${FOLDER_SIZE}  5GB

*** Test Cases ***
Copy Stap File Onto NAS
    # Fetch latest stap-scripts from git
    ErrInj: Stap: Fetch Stap Scripts From Git

    # Copy stap file onto NAS
    ${filePath}=  ErrInj: Stap: Search Stap File
    ...  filename=${STAP_FILE}  filter_str=${STAP_PATH}
    ${runStap}=  ErrInj: Stap: Copy Stap File Onto NAS  ${filePath}
    Set Global Variable  ${runStap}

Clean Environment
    # Kill all old stap processes and data
    ErrInj: Stap: Kill Stap Process On NAS
    # Clean up old data on NAS
    NAS: Setup: Clean Environment

Setup NAS Environment
    # Create test pool
    ${pool}=  NAS: Setup: Create Pool
    ...  disktype=${DISK_TYPE}
    ...  raid_level=${RAID_LEVEL}
    ...  raid_disk_num=${DISK_NUM}
    Set Global Variable  ${pool}

    # Create shared folder
    ${folder}=  NAS: Setup: Create ZFS shared folder
    ...  pool_id=${pool}
    ...  type=${FOLDER_TYPE}
    ...  size=${FOLDER_SIZE}
    Set Global Variable  ${folder}

    ${diskId}=  NAS: Utils: Get pool raid disks  ${pool}  spare=False
    Set Global Variable  ${diskId}

Create File In Folder & Fetch Inode Data
    # Create a file in folder
    ${testFile}=  NAS: Utils: Create Testfile  path=/share/${folder}
    Set Global Variable  ${testFile}
    # Fetch its inode data
    ${inode}=  NAS: Utils: Get file inode number  filepath=${testFile}
    Set Global Variable  ${inode}

Start STAP Testing
    # Setup parallel threads
    Threads: Add Thread
    ...  ErrInj: Stap: Run Stap File On NAS
    ...  filepath=${runStap}
    ...  options=${inode} 3 zpool2 -vg
    Threads: Add Thread
    ...  ErrInj: Stap: Wait Stap Process Start On NAS  acquire_lock=x-1
    Threads: Add Thread
    ...  NAS: Utils: Drop caches  acquire_lock=x-2
    Threads: Add Thread
    ...  NAS: Utils: Write testfile  filepath=${testFile}
    ...  acquire_lock=x-3

    #Start threads
    Threads: Start

Post-stap check expected pool and drives state
    ErrInj: Stap: Check stap pass on NAS
    ...  checkstr=injected write error 3 times
    NAS: Utils: Check error raid disks existence  ${diskId}  count=all
    ...  timeout=${300}
    NAS: Utils: Check expected pool existence
    ...  pool_id=${pool}
    ...  expected_status=Error
    ...  timeout=${900}

    #Kill stap process
    ErrInj: Stap: Kill Stap Process On NAS

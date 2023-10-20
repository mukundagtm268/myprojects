*** Settings ***
Documentation  A test suite to validate netback app
...            Created by Mukunda
Resource     ../Keywords/Main.robot
Library      Selenium2Library

Suite Setup   Run Keywords
...          Clean HDP Environment  ${URL}  ${CHROMEDRIVER_PATH}  ${NAS_USER}  ${NAS_PWD}
...    AND   NetBak: Launch app  ${CHROMEDRIVER_PATH}  ${APP_PATH}
...    AND   NetBak: Login app  ${NAS_IP}  ${NAS_USER}  ${NAS_PWD}
...    AND   NetBak: Create backup job  ${SHARED_FOLDER}  ${REPO_NAME}  ${DRIVE_LETTER}
...    AND   NetBak: Close app

Test Setup   Run Keywords
...          NetBak: Launch app  ${CHROMEDRIVER_PATH}  ${APP_PATH}
...    AND   NetBak: Login app  ${NAS_IP}  ${NAS_USER}  ${NAS_PWD}

Test Teardown  NetBak: Close app

*** Variables ***
# App Paths
${CHROMEDRIVER_PATH}  C:\\Users\\Dell\\Netback_Agent\\timeback_automation\\chromedriver.exe
${APP_PATH}  C:\\Program Files\\QNAP\\NetBakPCAgent\\App\\NetBak PC Agent.exe

# NAS data
${NAS_IP}      ${None}
${NAS_USER}    admin
${NAS_PWD}     ${None}

# Volume and REPO data
${DRIVE_LETTER}     ${None}
${SHARED_FOLDER}    NB_SharedFolder
${REPO_NAME}    NB_REPO

# Browser data
${BROWSER}  Chrome
${URL}      http://${NAS_IP}:8080/HyperDataProtector/#/

# Generic data
${EXPECTED_JOB_STATUS_AFTER_DISABLE}  Backup job aborted.
${BACKUP_JOB_STOPPED_TEXT}  Stopped

*** Test Cases ***
Launch HDP browser
    ${webDriver}  ${mouseDriver}=  HDP: Launch browser
    ...  url=${URL}
    ...  chromedriver_path=${CHROMEDRIVER_PATH}
    HDP: Login: Login HDP
    ...  driver=${webDriver}
    ...  username=${NAS_USER}
    ...  password=${NAS_PWD}

    Set Global Variable  ${webDriver}
    Set Global Variable  ${mouseDriver}

Validate NB repo state after detach from HDP
    HDP: Repository: Detach repository  ${webDriver}  ${REPO_NAME}
    NetBak: Validate NB repo state after detach from HDP
    HDP: Repository: Attach repository  ${webDriver}  ${REPO_NAME}

Validate NetBak backup job state after disabled from HDP
    ${jobName}  ${repositoryName}  ${inventoryName}=  NetBak: Get backup job details
    HDP: backup: Disable backup job
    ...  driver=${webDriver}
    ...  job_name=${jobName}
    NetBak: Validate backup job state after disabled from HDP

Validate NetBak backup job state after enable from HDP
    NetBak: Validate expected backup job status
    ...  expected_status=${EXPECTED_JOB_STATUS_AFTER_DISABLE}
    ${jobName}  ${repositoryName}  ${inventoryName}=  NetBak: Get backup job details
    HDP: backup: Enable backup job
    ...  driver=${webDriver}
    ...  job_name=${jobName}
    NetBak: Validate NetBak backup job state after enabled from HDP

Validate NetBak backup job state after stopped from HDP
    ${jobName}  ${repositoryName}  ${inventoryName}=  NetBak: Get backup job details
    NetBak: Start backup job
    HDP: Backup: stop backup job
    ...  driver=${webDriver}
    ...  mouse_driver=${mouseDriver}
    ...  job_name=${jobName}
    NetBak: Validate expected backup job status
    ...  expected_status=${BACKUP_JOB_STOPPED_TEXT}

Validate NB and HDP Job sync status, Detach and Attach Repositories after stopping job
    # Validate for mulitple times login
    NetBak: Start backup job
    NetBak: Close app
    NetBak: Launch app  ${CHROMEDRIVER_PATH}  ${APP_PATH}
    NetBak: Login app  ${NAS_IP}  ${NAS_USER}  ${NAS_PWD}
    ${jobName}  ${repositoryName}  ${inventoryName}=  NetBak: Get backup job details
    # Get HDP job status and validate
    ${HDPJobStatus}=  HDP: Backup: Get job status
    ...  ${webDriver}  ${mouseDriver}  ${jobName}
    NetBak: Validate expected backup job status
    ...  expected_status=${HDPJobStatus}
    NetBak: Stop backup job
    HDP: Repository: Detach repository  ${webDriver}  ${repositoryName}
    HDP: Repository: Attach repository  ${webDriver}  ${repositoryName}

Detach and attach Repo while job running
    NetBak: Start backup job
    ${jobName}  ${repositoryName}  ${inventoryName}=  NetBak: Get backup job details
    # Detach repo automatically stops the runnign job,
    # so need not to explicitly stop the job
    HDP: Repository: Detach repository  ${webDriver}  ${repositoryName}
    HDP: Repository: Attach repository  ${webDriver}  ${repositoryName}

Validate HDP and NB volumes sync in default job and edit job
    # Validate volumes in default job
    ${jobName}  ${repositoryName}  ${inventoryName}=  NetBak: Get backup job details
    # Get HDP job volumes
    @{HDPVolumes}=  HDP: Backup: Get HDP job volumes
    ...  driver=${webDriver}
    ...  job_name=${jobName}
    # Validate HDP and NB volumes
    NetBak: Validate NB and HDP job volumes sync
    ...  hdp_volumes=@{HDPVolumes}

    # Validate volumes after edit job
    NetBak: Edit backup job
    ...  drive_letter=${DRIVE_LETTER}
    @{HDPVolumes}=  HDP: Backup: Get HDP job volumes
    ...  driver=${webDriver}
    ...  job_name=${jobName}
    # Validate HDP and NB volumes
    NetBak: Validate NB and HDP job volumes sync
    ...  hdp_volumes=@{HDPVolumes}

Validate Refresh logs and date time sync for HDP and NetBak after login
     # Validate NetBak logs after login
     ${jobName}  ${repositoryName}  ${inventoryName}=  NetBak: Get backup job details
     NetBak: Validate logs after login
     ...  inv_name=${inventoryName}
     ...  repo_name=${repositoryName}
     # Validate HDP logs after login
     HDP: System: Validate HDP logs after NetBak login
     ...  driver=${webDriver}
     ...  inv_name=${inventoryName}
     ...  repo_name=${repositoryName}
     # Get Date time of logs from HDP
     ${HDPLogs}=  HDP: System: Get date time for HDP logs after NetBak login
     ...  driver=${webDriver}
     ...  inv_name=${inventoryName}
     ...  repo_name=${repositoryName}
     # Validate date time of NB and HDP synced
     NetBak: Validate NetBak HDP date time logs
     ...  hdp_logs=${HDPLogs}
     ...  inv_name=${inventoryName}
     ...  repo_name=${repositoryName}

Delete inventory while job running
    ${jobName}  ${repositoryName}  ${inventoryName}=  NetBak: Get backup job details
    NetBak: Start backup job
    HDP: Inventory: Delete inventory  ${webDriver}  ${inventoryName}

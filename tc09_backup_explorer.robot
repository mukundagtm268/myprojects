*** Settings ***
Documentation  A test suite to validate netback app
...            Created by Chandru
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
${APP_PATH}     C:\\Program Files\\QNAP\\NetBakPCAgent\\App\\NetBak PC Agent.exe

# NAS data
${NAS_IP}      ${None}
${NAS_USER}    admin
${NAS_PWD}     ${None}

# HDP data
${BROWSER}  Chrome
${URL}      http://${NAS_IP}:8080/HyperDataProtector/#/
${REMOTE_EXECUTION}  ${False}

# Repository data
${DRIVE_LETTER}     C
${SHARED_FOLDER}    netback_repo
${REPO_NAME}    ${None}

# Job data
${JOB_STATUS_TIMEOUT}  1200
${JOB_SUCCESSFUL}	Successful
${COUNT_SINGLE}     1
${COUNT_MULTI}     2

*** Test Cases ***
Validating No data popup when no backup job is Ran
    # Validating download button disable no jobs were selected
    ${webDriver}  ${mouseDriver}=  Launch Browser and Login HDP
    ...  url=${URL}
    ...  chromedriverPath=${CHROMEDRIVER_PATH}
    ...  nasUser=${NAS_USER}
    ...  nasPwd=${NAS_PWD}
    ...  openExplorer=${True}

    # No Data Popup validate
    HDP: Backup Explorer: Validate No Data Popup
    ...  driver=${webDriver}

Run job till successful and validate HDP job status
    # Start job and wait till successful
    NetBak: Start backup job
    NetBak: Validate expected backup job status
    ...  timeout=${JOB_STATUS_TIMEOUT}
    ...  expected_status=${JOB_SUCCESSFUL}
    ${jobName}  ${repositoryName}  ${inventoryName}=  NetBak: Get backup job details

    # Get HDP jb status and validate
    ${webDriver}  ${mouseDriver}=  Launch Browser and Login HDP
    ...  url=${URL}
    ...  chromedriverPath=${CHROMEDRIVER_PATH}
    ...  nasUser=${NAS_USER}
    ...  nasPwd=${NAS_PWD}
    ${HDPJobStatus}=  HDP: Backup: Get job status
    ...  ${webDriver}  ${mouseDriver}  ${jobName}
    NetBak: Validate expected backup job status
    ...  expected_status=${HDPJobStatus}

Validating download button disable
    # Validating download button disable no jobs were selected
    HDP: Backup Explorer: Open backup explorer
    ...  driver=${webDriver}

    # Validating download button disable
    HDP: Backup Explorer: Validate download disable
    ...  driver=${webDriver}

Download file from explorer
    ${webDriver}  ${mouseDriver}=  Launch Browser and Login HDP
    ...  url=${URL}
    ...  chromedriverPath=${CHROMEDRIVER_PATH}
    ...  nasUser=${NAS_USER}
    ...  nasPwd=${NAS_PWD}
    ...  openExplorer=${True}

    HDP: Backup Explorer: Download file
    ...  driver=${webDriver}
    ...  mouse_driver=${mouseDriver}
    ...  drive_letter=${DRIVE_LETTER}

Validate tooltip for single backup job
    # Open Explorer in HDP and validate tooltip
    ${webDriver}  ${mouseDriver}=  Launch Browser and Login HDP
    ...  url=${URL}
    ...  chromedriverPath=${CHROMEDRIVER_PATH}
    ...  nasUser=${NAS_USER}
    ...  nasPwd=${NAS_PWD}
    ...  openExplorer=${True}
    HDP: Validate Tooltip Job
    ...  driver=${webDriver}
    ...  count=${count_single}

Download job status report for Successful job
    NetBak: Download job status report
    ...  expected_state=${JOB_SUCCESSFUL}

Validate Calendar Scroll Dates
    ${webDriver}  ${mouseDriver}=  Launch Browser and Login HDP
    ...  url=${URL}
    ...  chromedriverPath=${CHROMEDRIVER_PATH}
    ...  nasUser=${NAS_USER}
    ...  nasPwd=${NAS_PWD}
    ...  openExplorer=${True}
    HDP: Backup Explorer: Validate calendar scroll dates
    ...  driver=${webDriver}

Validate Current date selected in Left Calendar
    ${webDriver}  ${mouseDriver}=  Launch Browser and Login HDP
    ...  url=${URL}
    ...  chromedriverPath=${CHROMEDRIVER_PATH}
    ...  nasUser=${NAS_USER}
    ...  nasPwd=${NAS_PWD}
    ...  openExplorer=${True}
    HDP: Backup Explorer: Validate current date in left calendar
    ...  driver=${webDriver}

Validate selecting options Year/Month from right Calendar
    ${webDriver}  ${mouseDriver}=  Launch Browser and Login HDP
    ...  url=${URL}
    ...  chromedriverPath=${CHROMEDRIVER_PATH}
    ...  nasUser=${NAS_USER}
    ...  nasPwd=${NAS_PWD}
    ...  openExplorer=${True}
    HDP: Backup Explorer: Validate options in right Calendar
    ...  ${webDriver}

Run job till successful and validate HDP job status 2
    # Start job and wait till successful
    NetBak: Start backup job
    ...  rerun=${True}
    NetBak: Validate expected backup job status
    ...  timeout=${JOB_STATUS_TIMEOUT}
    ...  expected_status=${JOB_SUCCESSFUL}
    ${jobName}  ${repositoryName}  ${inventoryName}=  NetBak: Get backup job details

    # Get HDP jb status and validate
    ${webDriver}  ${mouseDriver}=  Launch Browser and Login HDP
    ...  url=${URL}
    ...  chromedriverPath=${CHROMEDRIVER_PATH}
    ...  nasUser=${NAS_USER}
    ...  nasPwd=${NAS_PWD}
    ${HDPJobStatus}=  HDP: Backup: Get job status
    ...  ${webDriver}  ${mouseDriver}  ${jobName}
    NetBak: Validate expected backup job status
    ...  expected_status=${HDPJobStatus}

Validate tooltip for multiple backup job
    # Open Explorer in HDP and validate tooltip
    ${webDriver}  ${mouseDriver}=  Launch Browser and Login HDP
    ...  url=${URL}
    ...  chromedriverPath=${CHROMEDRIVER_PATH}
    ...  nasUser=${NAS_USER}
    ...  nasPwd=${NAS_PWD}
    ...  openExplorer=${True}
    HDP: Validate Tooltip Job
    ...  driver=${webDriver}
    ...  count=${COUNT_MULTI}

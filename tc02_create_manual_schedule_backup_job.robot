*** Settings ***
Documentation  A test suite to validate netback app
...            Created by Mukunda
Resource     ../Keywords/Main.robot
Library      Selenium2Library

Test Setup   Run Keywords
...          Clean HDP Environment  ${URL}  ${CHROMEDRIVER_PATH}  ${NAS_USER}  ${NAS_PWD}
...    AND   NetBak: Launch app  ${CHROMEDRIVER_PATH}  ${APP_PATH}
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

# HDP data
${BROWSER}  Chrome
${URL}      http://${NAS_IP}:8080/HyperDataProtector/#/
${REMOTE_EXECUTION}  ${False}

# Repository data
${DRIVE_LETTER}    ${None}
${SHARED_FOLDER}   NB_SharedFolder
${REPO_NAME}       NB_REPO

# Daily Schedule data
${SCHEDULE_OPTION}  Every weekday

# Generic Data
${ITERATION}  4

*** Test Cases ***
Create Backup job without schedule
    NetBak: Create backup job
    ...  drive_letter=${DRIVE_LETTER}
    ...  shared_folder=${SHARED_FOLDER}
    ...  repo_name=${REPO_NAME}
    NetBak: Start backup job
    NetBak: Check backup job status
    NetBak: Stop backup job

Schedule Daily Backup Job
    NetBak: Schedule daily backup job
    ...  schedule_option=${SCHEDULE_OPTION}
    ...  drive_letter=${DRIVE_LETTER}
    ...  shared_folder=${SHARED_FOLDER}
    ...  repo_name=${REPO_NAME}
    NetBak: Start backup job
    NetBak: Check backup job status
    NetBak: Stop backup job

Schedule Monthly Backup Job
    NetBak: Schedule monthly backup job
    ...  drive_letter=${DRIVE_LETTER}
    ...  shared_folder=${SHARED_FOLDER}
    ...  repo_name=${REPO_NAME}
    NetBak: Start backup job
    NetBak: Check backup job status
    NetBak: Stop backup job

Validate Next button Greyed out after deselecting Volumes
    NetBak: Validate next button after deselecting volumes
    ...  shared_folder=${SHARED_FOLDER}
    ...  repo_name=${REPO_NAME}

Validate Backup functionality after multiple login
    NetBak: Create backup job
    ...  drive_letter=${DRIVE_LETTER}
    ...  shared_folder=${SHARED_FOLDER}
    ...  repo_name=${REPO_NAME}
    NetBak: Close app
    NetBak: Validate backup functionality after multiple login
    ...  iteration=${ITERATION}
    ...  chromedriver_path=${CHROMEDRIVER_PATH}
    ...  app_path=${APP_PATH}
    ...  nas_ip=${NAS_IP}
    ...  username=${NAS_USER}
    ...  password=${NAS_PWD}

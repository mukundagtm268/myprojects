*** Settings ***
Documentation  A test suite to validate netback app
...            Created by Sachin
Resource     ../Keywords/Main.robot
Library      Selenium2Library

Suite Setup  Clean HDP Environment  ${URL}  ${CHROMEDRIVER_PATH}  ${NAS_USER}  ${NAS_PWD}

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

# HDP data
${BROWSER}  Chrome
${URL}      http://${NAS_IP}:8080/HyperDataProtector/#/
${REMOTE_EXECUTION}  ${False}

# Repository data
${DRIVE_LETTER}     ${None}
${SHARED_FOLDER}    Netbak_Repo
${REPO_NAME}        netbak_repo

*** Test Cases ***
Create Backup Job
    NetBak: Create backup job
    ...  drive_letter=${DRIVE_LETTER}
    ...  shared_folder=${SHARED_FOLDER}
    ...  repo_name=${REPO_NAME}

Validate home tabs after backup job
    NetBak: Validate home tabs after backup job
    ...  username=${NAS_USER}

Validate Overview page details
    NetBak: Validate overview page
    ...  username=${NAS_USER}
    ...  nas_ip=${NAS_IP}
    ...  repository_name=${REPO_NAME}

Validate Network IP and Host IP
    ${networkIP}=  NetBak: Get network IP from overview page
    NetBak: Validate network IP with host IP
    ...  network_ip=${networkIP}

Validate Job History page details
    NetBak: Validate job history page fields

Validate Logs page details
    NetBak: Validate logs page fields
    NetBak: Validate user name of logs
    ...  nas_user=${NAS_USER}

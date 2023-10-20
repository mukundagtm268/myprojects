*** Settings ***
Documentation  A test suite to validate netback app
...            Created by Sachin
Resource     ../Keywords/Main.robot
Library      Selenium2Library

Test Setup   Run Keywords
...          Clean HDP Environment  ${URL}  ${CHROMEDRIVER_PATH}  ${NAS_USER}  ${NAS_PWD}
...    AND   NetBak: Launch app  ${CHROMEDRIVER_PATH}  ${APP_PATH}

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

*** Test Cases ***
Create Backup after login through LAN with Admin role first time
    NetBak: Login app using LAN
    ...  nas_ip=${NAS_IP}
    ...  username=${NAS_USER}
    ...  password=${NAS_PWD}
    NetBak: Create backup job
    ...  drive_letter=${DRIVE_LETTER}
    ...  shared_folder=${SHARED_FOLDER}
    ...  repo_name=${REPO_NAME}

Create Backup after login through LAN with Admin role second time
    NetBak: Login app using LAN
    ...  nas_ip=${NAS_IP}
    ...  username=${NAS_USER}
    ...  password=${NAS_PWD}
    NetBak: Create backup job
    ...  drive_letter=${DRIVE_LETTER}
    ...  shared_folder=${SHARED_FOLDER}
    ...  repo_name=${REPO_NAME}

Logout from normal login, relogin using LAN
    NetBak: Login app
    ...  nas_ip=${NAS_IP}
    ...  username=${NAS_USER}
    ...  password=${NAS_PWD}
    NetBak: Create backup job
    ...  drive_letter=${DRIVE_LETTER}
    ...  shared_folder=${SHARED_FOLDER}
    ...  repo_name=${REPO_NAME}
    NetBak: Logout app
    NetBak: Press back button in credentials page
    NetBak: Login app using LAN
    ...  nas_ip=${NAS_IP}
    ...  username=${NAS_USER}
    ...  password=${NAS_PWD}

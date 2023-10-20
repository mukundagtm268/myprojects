*** Settings ***
Documentation  A test suite to validate netback app
...            Created by Sachin
Resource     ../Keywords/Main.robot
Library      Selenium2Library

Test Setup   Run Keywords
...          Clean HDP Environment  ${URL}  ${CHROMEDRIVER_PATH}  ${NAS_USER}  ${NAS_PWD}
...    AND   NetBak: Launch app  ${CHROMEDRIVER_PATH}  ${APP_PATH}
...    AND   NetBak: Login app  ${NAS_IP}  ${NAS_USER}  ${NAS_PWD}
...    AND   NetBak: Create backup job  ${SHARED_FOLDER}  ${REPO_NAME}  ${DRIVE_LETTER}

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

# Network Details
${AUTO_NETWORK_TYPE}    automatic
${MANUAL_NETWORK_TYPE}  manual
${WIFI_MANUAL_CONFIG}   wifi
${ETHER_MANUAL_CONFIG}  ethernet

*** Test Cases ***
Select Automatic Network Config
    NetBak: Edit backup job
    ...  network_type=${AUTO_NETWORK_TYPE}

Select Manual Wifi Network Config
    NetBak: Edit backup job
    ...  network_type=${MANUAL_NETWORK_TYPE}
    ...  manual_config=${WIFI_MANUAL_CONFIG}

Select Manual Ethernet Network Config
    NetBak: Edit backup job
    ...  network_type=${MANUAL_NETWORK_TYPE}
    ...  manual_config=${ETHER_MANUAL_CONFIG}
